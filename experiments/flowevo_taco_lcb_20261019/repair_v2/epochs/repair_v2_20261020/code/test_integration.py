"""Linux/bubblewrap integration tests with real candidate-visible I/O and isolation."""
import pathlib,tempfile,unittest
from sandbox import Worker

class Integration(unittest.TestCase):
 def run_candidate(self,source,request):
  with tempfile.NamedTemporaryFile(mode='w',suffix='.py') as f:
   f.write(source);f.flush()
   with Worker(f.name) as w:
    if request['mode']=='stdio':
     r=w.call({'mode':'compile_stdio','timeout':2});self.assertEqual(r['status'],'OK')
    return w.call(request)
 def test_bytes_readline_eof_stdout(self):
  s='import sys\na=sys.stdin.buffer.readline(); b=sys.stdin.buffer.readline(); c=sys.stdin.buffer.readline(); sys.stdout.buffer.write(a+b+c)'
  r=self.run_candidate(s,{'mode':'stdio','timeout':2,'input':'first\nsecond\n'});self.assertEqual(r['status'],'OK');self.assertEqual(r['output'],'first\nsecond\n')
 def test_os_read(self):
  r=self.run_candidate('import os\nos.write(1,os.read(0,1000))',{'mode':'stdio','timeout':2,'input':'real descriptors'});self.assertEqual(r['output'],'real descriptors')
 def test_large_valid_output(self):
  r=self.run_candidate('import sys\nsys.stdout.write("x"*3000000)',{'mode':'stdio','timeout':3,'input':''});self.assertEqual(r['status'],'OK');self.assertEqual(len(r['output']),3000000)
 def test_hidden_answers_absent(self):
  s='import os\nprint(os.path.exists("/task.json"), os.path.exists("/root/.deepseek-key"))'
  r=self.run_candidate(s,{'mode':'stdio','timeout':2,'input':''});self.assertEqual(r['output'].strip(),'False False')
 def test_timeout(self):
  r=self.run_candidate('while True: pass',{'mode':'stdio','timeout':0.1,'input':''});self.assertEqual(r['status'],'TIME_LIMIT')
 def test_function_return(self):
  r=self.run_candidate('class Solution:\n def f(self,a: List[int])->int:\n  return sum(a)',{'mode':'function','function':'f','args':[[2,3]],'timeout':2});self.assertEqual(r['status'],'OK');self.assertEqual(r['value'],5)
 def test_function_exception(self):
  r=self.run_candidate('def f(x):\n return 1/0',{'mode':'function','function':'f','args':[1],'timeout':2});self.assertEqual(r['status'],'RUNTIME_ERROR');self.assertIn('ZeroDivisionError',r['error'])
 def test_function_state(self):
  with tempfile.NamedTemporaryFile(mode='w',suffix='.py') as f:
   f.write('n=0\ndef f(x):\n global n\n n+=x\n return n');f.flush()
   with Worker(f.name) as w:
    for x,y in [(2,2),(3,5)]:self.assertEqual(w.call({'mode':'function','function':'f','args':[x],'timeout':2})['value'],y)

if __name__=='__main__':unittest.main(verbosity=2)
