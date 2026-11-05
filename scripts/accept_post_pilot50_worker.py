"""Zero-model API isolation probes through the existing DockerWorker."""
import json,tempfile,time
from pathlib import Path
from run_math_v3_development import IMAGE,WORKER,ROOT
from failure_evo.container_worker import DockerWorker
from failure_evo.contracts import fingerprint

def main():
 out=ROOT/'reports/post_pilot50_end_to_end/worker_acceptance.json'
 probes={
 'normal':"def probe(): return 3",
 'network':"import socket\ndef probe():\n s=socket.socket();s.settimeout(.2)\n try: s.connect(('192.0.2.1',443));return 'CONNECTED'\n except OSError: return 'BLOCKED'",
 'outside_write':"def probe():\n try:\n  open('/outside-probe','w').write('probe');return 'WROTE'\n except OSError: return 'BLOCKED'",
 'host_private':"def probe():\n try:\n  open('/Users/majiatong/.env').read();return 'READ'\n except OSError: return 'BLOCKED'",
 'output':"def probe(): return 'x' * (2*1024*1024)",
 'file_descriptors':"def probe():\n files=[]\n try:\n  for i in range(100): files.append(open('/dev/null'))\n except OSError: return 'LIMITED'\n return 'UNLIMITED'",
 'tmp_limit':"def probe():\n try:\n  with open('/tmp/probe','wb') as f:\n   for i in range(40): f.write(b'x'*1048576)\n  return 'UNLIMITED'\n except OSError: return 'LIMITED'",
 'loop':"def probe():\n while True: pass",
 'recursion':"def probe(): return probe()",
 }
 results=[]
 with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
  for name,code in probes.items():
   p=Path(tmp)/'candidate.py';p.write_text(code)
   started=time.monotonic()
   with DockerWorker(p,image=IMAGE,worker_script=WORKER) as w:
    raw=w.call(dict(mode='function',function='probe',args=[],timeout=1))
   results.append(dict(name=name,raw=raw,seconds=time.monotonic()-started,source_sha256=fingerprint(code)))
 out.write_text(json.dumps(dict(image=IMAGE,worker_sha256=fingerprint(WORKER.read_text()),results=results,api_calls=0),indent=2)+'\n')
 print(json.dumps(results))
if __name__=='__main__':main()
