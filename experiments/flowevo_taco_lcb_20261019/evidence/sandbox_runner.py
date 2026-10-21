import json, pathlib, subprocess, threading, time
ROOT=pathlib.Path(__file__).resolve().parent
EVAL_LOCK=threading.Semaphore(2)
def evaluate(task_path,code_path,num_tests):
 args=['bwrap','--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc/alternatives','/etc/alternatives','--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache','--ro-bind',str(ROOT/'vendor/eval_sources'),'/eval','--ro-bind',str(ROOT/'judge.py'),'/judge.py','--ro-bind',str(task_path),'/task.json','--ro-bind',str(code_path),'/candidate.py','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/sandboxbin','--symlink','/usr/bin/python3','/sandboxbin/python','--chdir','/tmp','--clearenv','--setenv','PATH','/sandboxbin:/usr/bin','--setenv','PYTHONHASHSEED','0','--setenv','OPENBLAS_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1','--uid','65534','--gid','65534','python3','/judge.py']
 with EVAL_LOCK:
  started=time.monotonic()
  # External timeout bounds the complete evaluator; individual case limits are 4s/6s.
  timeout=30+max(1,num_tests)*7
  try:p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
  except subprocess.TimeoutExpired: return {'passed':False,'feedback':'Evaluator total time limit exceeded.','timeout':True,'wall_seconds':time.monotonic()-started}
  lines=[x[len('BENCH_JUDGE='):] for x in p.stdout.splitlines() if x.startswith('BENCH_JUDGE=')]
  if p.returncode or not lines:raise RuntimeError('sandbox/evaluator error: '+p.stderr[-500:]+p.stdout[-200:])
  result=json.loads(lines[-1])
  if result.get('infrastructure_error'):raise RuntimeError(json.dumps(result))
  return result
