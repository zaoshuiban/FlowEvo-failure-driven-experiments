"""Docker-backed local Linux Worker. No candidate executes in host Python."""
import json
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import time
import uuid


class DockerWorker:
    def __init__(self, candidate, *, image, worker_script):
        if not shutil.which('docker'):
            raise RuntimeError('local Docker Linux runtime unavailable')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
            raise ValueError('locally inspected immutable Docker image ID required')
        context = json.loads(subprocess.check_output(['docker','context','inspect'],timeout=5))
        if not context[0]['Endpoints']['docker']['Host'].startswith('unix://') or os.environ.get('DOCKER_HOST','').startswith(('tcp:','ssh:')):
            raise RuntimeError('only a local Unix-socket Docker daemon is allowed')
        if subprocess.check_output(['docker','info','--format','{{.OSType}}'],timeout=5,text=True).strip() != 'linux':
            raise RuntimeError('Linux daemon required')
        candidate = Path(candidate).resolve()
        worker_script = Path(worker_script).resolve()
        for path in (candidate, worker_script):
            if not path.is_file() or ',' in str(path):
                raise ValueError('invalid read-only worker mount')
        self.name = 'flowevo-' + uuid.uuid4().hex
        self.buffer = b''
        self.closed = False
        args = ['docker','run','--rm','--pull=never','--name',self.name,'-i',
            '--network=none','--read-only','--cap-drop=ALL',
            '--security-opt=no-new-privileges','--pids-limit=32',
            '--memory=256m','--memory-swap=256m','--cpus=1',
            '--ulimit','nofile=64:64','--ulimit','nproc=32:32',
            '--ulimit','fsize=33554432:33554432','--ulimit','core=0:0',
            '--user=65534:65534','--tmpfs','/tmp:rw,noexec,nosuid,size=32m',
            '--workdir=/tmp',
            '--mount','type=bind,src='+str(candidate)+',dst=/candidate.py,readonly',
            '--mount','type=bind,src='+str(worker_script)+',dst=/worker.py,readonly',
            '--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONHASHSEED=0',
            '--entrypoint','python3',image,'-I','-u','/worker.py']
        self.process = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)

    def call(self, request):
        seconds = request.get('timeout', 5)
        if not isinstance(seconds,(int,float)) or not 0 < seconds <= 10:
            raise ValueError('worker timeout must be positive and at most 10 seconds')
        try:
            self.process.stdin.write(json.dumps(request).encode()+b'\n')
            self.process.stdin.flush()
            deadline = time.monotonic() + seconds + 2  # bounded container startup allowance
            while b'\n' not in self.buffer:
                wait = deadline-time.monotonic()
                if wait <= 0:
                    self.close()
                    return {'status':'TIME_LIMIT','origin':'host_deadline'}
                ready,_,_ = select.select([self.process.stdout],[],[],wait)
                if not ready:
                    continue
                chunk = os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    return {'status':'EVALUATOR_ERROR','reason':'isolated_worker_exited'}
                self.buffer += chunk
                if len(self.buffer) > 1024*1024:
                    self.close()
                    return {'status':'OUTPUT_LIMIT'}
            line,self.buffer = self.buffer.split(b'\n',1)
            value = json.loads(line)
            return value if isinstance(value,dict) else {'status':'EVALUATOR_ERROR'}
        except (OSError,ValueError):
            return {'status':'EVALUATOR_ERROR'}

    def close(self):
        if self.closed:return
        removed=False
        try:
            result=subprocess.run(['docker','rm','-f',self.name],stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
            removed=result.returncode==0
            if not removed:
                check=subprocess.run(['docker','ps','-a','--filter','name='+self.name,'--format','{{.ID}}'],
                    capture_output=True,text=True,timeout=5)
                removed=check.returncode==0 and not check.stdout.strip()
        finally:
            if self.process.poll() is None:self.process.kill()
            self.process.wait(timeout=5)
            for stream in (self.process.stdin,self.process.stdout):
                if not stream.closed:stream.close()
        if not removed:raise RuntimeError('container cleanup unconfirmed; stop study')
        self.closed=True

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
