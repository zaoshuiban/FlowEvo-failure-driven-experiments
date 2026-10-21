import contextlib, importlib, io, json, os, pathlib, resource, signal, sys, time
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
class LimitedCapture(io.TextIOBase):
 def __init__(self):self.text=''
 def write(self,s):self.text=(self.text+s)[-4000:];return len(s)
 def flush(self):pass
 def fileno(self):return sys.__stderr__.fileno()
 def writable(self):return True
raw=json.loads(pathlib.Path('/task.json').read_text())
tests=json.loads(raw['input_output'])
keep=[]
for i,s in enumerate(tests['inputs']):
 args=[json.loads(x) for x in s.split('\n')];points=args[0]
 if isinstance(points,list) and len(points)>=3 and all(isinstance(x,list) and len(x)==2 for x in points):keep.append(i)
tests['inputs']=[tests['inputs'][i] for i in keep];tests['outputs']=[tests['outputs'][i] for i in keep];raw['input_output']=json.dumps(tests)
code=pathlib.Path('/candidate.py').read_text()
num_tests=len(json.loads(raw['input_output'])['inputs'])
started=time.monotonic();capture=LimitedCapture()
try:
 with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
  if raw['dataset']=='taco':
   sys.path.insert(0,'/eval/TACO')
   from metrics import testing_util as judge
   # Stop after the first failed case; the all-tests-pass predicate is unchanged.
   for name in ['execute_cb_code','execute_std_code']:
    original=getattr(judge,name)
    def early(*args,_original=original,**kwargs):
     kwargs['early_stop']=True
     return _original(*args,**kwargs)
    setattr(judge,name,early)
   values=judge.run_test({'input_output':raw['input_output']},test=code,debug=raw.get("debug",False))
   metadata={}
  else:
   sys.path.insert(0,'/eval/LiveCodeBench/lcb_runner/evaluation')
   import testing_util as judge
   values,metadata=judge.run_test({'input_output':raw['input_output']},test=code,debug=False,timeout=6)
  signal.alarm(0)
  values=[int(x) for x in values]
  passed=len(values)==num_tests and all(x==1 for x in values)
  bad=next((x for x in values if x!=1),None)
  feedback='All tests passed.' if passed else {0:'Wrong answer.',-1:'Time limit exceeded.',-2:'Runtime or compilation error.',-3:'Runtime error.',-4:'Compilation or testing error.'}.get(bad,'Incomplete test execution.')
  result={'official_metadata':metadata,'captured_output':capture.text,'passed':passed,'feedback':feedback,'tests_total':num_tests,'tests_reported':len(values),'tests_passed':sum(x==1 for x in values),'result_codes':dict(__import__('collections').Counter(map(str,values))),'wall_seconds':round(time.monotonic()-started,4)}
except BaseException as e:
 signal.alarm(0)
 result={'passed':False,'infrastructure_error':True,'error_type':type(e).__name__,'error_message':str(e)[:200],'feedback':'Evaluator infrastructure error.','wall_seconds':round(time.monotonic()-started,4)}
if raw.get('debug'):result['debug_output']=capture.text
print('BENCH_JUDGE='+json.dumps(result),flush=True)
