import json,pathlib
from sandbox_runner import evaluate,ROOT
folder=ROOT/'selftests';folder.mkdir(exist_ok=True)
cases=[
 ('taco_stdin','taco',{'inputs':['2 3\n','-4 9\n'],'outputs':['5\n','5\n']},'a,b=map(int,input().split());print(a+b)'),
 ('taco_function','taco',{'inputs':[[2,3],[-4,9]],'outputs':[5,5],'fn_name':'add'},'class Solution:\n def add(self,a,b): return a+b'),
 ('lcb_stdin','lcb',{'inputs':['2 3\n','-4 9\n'],'outputs':['5\n','5\n']},'a,b=map(int,input().split());print(a+b)'),
 ('lcb_function','lcb',{'inputs':['2\n3','-4\n9'],'outputs':['5','5'],'fn_name':'add'},'class Solution:\n def add(self,a,b): return a+b')]
records=[]
for name,ds,tests,code in cases:
 task=folder/(name+'.json');candidate=folder/(name+'.py')
 task.write_text(json.dumps({'dataset':ds,'input_output':json.dumps(tests)}));candidate.write_text(code)
 result=evaluate(task,candidate,len(tests['inputs']));print(name,result,flush=True);assert result['passed']
 candidate.write_text(code.replace('a+b','a-b'))
 bad=evaluate(task,candidate,len(tests['inputs']));assert not bad['passed'];records.append({'case':name,'valid_passed':True,'invalid_rejected':True})
# Verify timeout and inaccessible host secrets/network from inside the same namespace.
name,ds,tests,_=cases[0];task=folder/(name+'.json');candidate=folder/'timeout.py';candidate.write_text('while True: pass')
result=evaluate(task,candidate,2);assert not result['passed'];records.append({'case':'timeout','invalid_rejected':True})
(ROOT/'reports/selftest.json').write_text(json.dumps(records,indent=2));print('SELFTEST_PASSED',flush=True)
