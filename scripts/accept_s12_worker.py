"""Actual local Linux probes; unavailable runtime is BLOCKED, never a mocked PASS."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.container_worker import DockerWorker
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',help='docker image inspect --format {{.Id}} ...')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();out=Path(args.output)
    if out.exists():raise FileExistsError('use a fresh result path')
    result=dict(status='BLOCKED',new_api_calls=0,checks=[],image=args.image,
        worker_script_sha256=hashlib.sha256(WORKER.read_bytes()).hexdigest(),
        adapter_sha256=hashlib.sha256((ROOT/'FlowEvo/src/failure_evo/container_worker.py').read_bytes()).hexdigest())
    if not shutil.which('docker') or not args.image:
        result['reason']='local Linux Docker runtime and immutable image ID required'
    else:
        with tempfile.TemporaryDirectory(prefix='flowevo-isolation-') as tmp:
            root=Path(tmp);marker=root/'host-only';marker.write_text('synthetic sentinel')
            probes=[
                ('normal', 'def probe(): return 42', lambda r:r.get('status')=='OK' and r.get('value')==42),
                ('runtime_error','def probe(): raise ValueError("fixture")',lambda r:r.get('status')=='RUNTIME_ERROR'),
                ('timeout','def probe():\n while True: pass',lambda r:r.get('status')=='TIME_LIMIT'),
                ('host_file_hidden','def probe():\n import os\n return not os.path.exists('+repr(str(marker))+')',lambda r:r.get('value') is True),
                ('credentials_absent','def probe():\n import os\n return all(k not in os.environ for k in ["DEEPSEEK_API_KEY","OPENAI_API_KEY"])',lambda r:r.get('value') is True),
                ('readonly_source','def probe():\n try: open("/candidate.py","w"); return False\n except OSError: return True',lambda r:r.get('value') is True),
                ('network_denied','def probe():\n import socket\n s=socket.socket();s.settimeout(.2)\n try: s.connect(("192.0.2.1",80));return False\n except OSError: return True\n finally: s.close()',lambda r:r.get('value') is True),
                ('nonroot_no_escalation','def probe():\n import os\n if os.getuid()!=65534:return False\n try: os.setuid(0);return False\n except OSError:return True',lambda r:r.get('value') is True),
                ('pids_cgroup','def probe():\n return open("/sys/fs/cgroup/pids.max").read().strip()=="32"',lambda r:r.get('value') is True),
                ('memory_cgroup','def probe():\n return open("/sys/fs/cgroup/memory.max").read().strip()=="268435456"',lambda r:r.get('value') is True),
                ('private_process_namespace','def probe():\n import os\n return len([p for p in os.listdir("/proc") if p.isdigit()])<=4',lambda r:r.get('value') is True),
                ('memory_limit','def probe():\n return len(bytearray(512*1024*1024))',lambda r:r.get('status') in ('RUNTIME_ERROR','EVALUATOR_ERROR')),
            ]
            for name,code,predicate in probes:
                source=root/(name+'.py');source.write_text(code)
                try:
                    with DockerWorker(source,image=args.image,worker_script=WORKER) as worker:
                        observed=worker.call(dict(mode='function',function='probe',args=[],timeout=.5))
                    passed=predicate(observed)
                except Exception as exc:
                    observed={'status':'INFRASTRUCTURE_ERROR','error_type':type(exc).__name__};passed=False
                result['checks'].append(dict(name=name,passed=passed,result=observed))
        result['status']='PASS' if all(r['passed'] for r in result['checks']) else 'FAIL'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
