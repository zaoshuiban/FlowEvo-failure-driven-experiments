"""Host-side controller. Expected outputs stay outside the candidate namespace."""
import json
import os
import pathlib
import select
import subprocess
import time

CODE = pathlib.Path(__file__).resolve().parent


class Worker:
    def __init__(self, candidate):
        self.buffer=b''
        args=['bwrap','--unshare-all','--die-with-parent','--new-session',
              '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin',
              '--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64',
              '--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache',
              '--ro-bind',str(CODE/'candidate_worker.py'),'/worker.py',
              '--ro-bind',str(pathlib.Path(candidate).resolve()),'/candidate.py',
              '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir','/tmp',
              '--clearenv','--setenv','PATH','/usr/bin','--setenv','PYTHONHASHSEED','0',
              '--setenv','OPENBLAS_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1',
              '--uid','65534','--gid','65534','python3','-u','/worker.py']
        self.process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    def call(self,request):
        try:
            self.process.stdin.write(json.dumps(request,ensure_ascii=True).encode()+b'\n')
            self.process.stdin.flush()
            deadline=time.monotonic()+request.get('timeout',6)+20
            while b'\n' not in self.buffer:
                wait=deadline-time.monotonic()
                if wait<=0:return {'status':'EVALUATOR_ERROR','error':'worker protocol deadline'}
                ready,_,_=select.select([self.process.stdout],[],[],wait)
                if not ready:continue
                chunk=os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    return {'status':'EVALUATOR_ERROR','error':'worker exited','stderr':self.process.stderr.read(8000).decode(errors='replace')}
                self.buffer+=chunk
                if len(self.buffer)>64*1024**2:return {'status':'EVALUATOR_ERROR','error':'worker protocol output too large'}
            line,self.buffer=self.buffer.split(b'\n',1)
            response=json.loads(line)
            if response.get('status')=='WORKER_ERROR':response['status']='EVALUATOR_ERROR'
            return response
        except (OSError,ValueError) as exc:return {'status':'EVALUATOR_ERROR','error':repr(exc)}

    def close(self):
        try:self.process.stdin.close()
        except OSError:pass
        try:self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.process.stdout.close();self.process.stderr.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
