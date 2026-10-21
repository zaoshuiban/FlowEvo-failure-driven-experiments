"""Private hidden evaluator. Candidate receives stdin only, never expected values."""
import ast,collections,hashlib,json,pathlib,re,sys
from decimal import Decimal,InvalidOperation
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from sandbox import Worker
from adapter import evaluate_v2
from regrade import write

def extract(text):
 # Preserve historical extraction behavior: truncated/unclosed blocks are not silently repaired.
 matches=re.findall(r'```(?:python|py)?\s*\n(.*?)```',text,re.S|re.I)
 if matches:return matches[-1].strip()+'\n'
 if '```' in text:return text.strip()+'\n'
 return text.strip()+'\n' if text.strip() else ''
def compare(actual,case):
 got=actual.split();expected=case['expected']
 if len(got)!=len(expected):return False
 if case['comparison']=='integer_tokens':return got==expected
 try:return all(re.fullmatch(r'-?\d+\.\d{4}',a) and Decimal(a).is_finite() and abs(Decimal(a)-Decimal(b))<=Decimal('0.0000500001') for a,b in zip(got,expected))
 except InvalidOperation:return False

def evaluate(code,tid):
 source=code.read_text()
 if not source.strip():return {'status':'NO_COMPLETE_CODE','passed':False}
 try:ast.parse(source)
 except SyntaxError as exc:return {'status':'COMPILE_ERROR','passed':False,'error':str(exc)}
 cases=json.loads((ROOT/'e2_frozen/hidden'/(tid+'.json')).read_text());count=0
 with Worker(code) as w:
  v=w.call({'mode':'compile_stdio','timeout':6})
  if v['status']!='OK':return {'status':v['status'],'passed':False,'diagnostic':v}
  for c in cases:
   v=w.call({'mode':'stdio','input':c['input'],'timeout':4 if tid.startswith('taco') else 6})
   if v['status']!='OK':return {'status':v['status'],'passed':False,'private_failed_index':c['index'],'diagnostic':v,'tests_passed':count,'total_tests':len(cases)}
   if not compare(v['output'],c):return {'status':'WRONG_ANSWER','passed':False,'private_failed_index':c['index'],'actual_preview':v['output'][:1000],'tests_passed':count,'total_tests':len(cases)}
   count+=1
 return {'status':'PASS','passed':True,'tests_passed':count,'total_tests':len(cases)}

def main():
 calls=json.loads((ROOT/'e2_frozen/calls.json').read_text());results=[]
 for c in calls:
  dest=ROOT/'e2_results/grades'/(c['call_id']+'.json');response=ROOT/'e2_results/responses'/(c['call_id']+'.json')
  if not response.exists():continue
  if dest.exists():results.append(json.loads(dest.read_text()));continue
  raw=json.loads(response.read_text());text=raw['choices'][0]['message'].get('content') or '';code=ROOT/'e2_results/programs'/(c['call_id']+'.py');code.parent.mkdir(parents=True,exist_ok=True);code.write_text(extract(text));audited=evaluate(code,c['task_id']);original=evaluate_v2(BASE/'data/tasks'/(c['task_id']+'.json'),code,BASE/'repair_v2d_20261020/policies.json')
  row={'call_id':c['call_id'],'task_id':c['task_id'],'condition':c['condition'],'repeat':c['repeat'],'audited_hidden':audited,'original_v2_hidden':original,'code_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'usage':raw.get('usage'),'model':raw.get('model'),'finish_reason':raw['choices'][0].get('finish_reason')}
  write(dest,row);results.append(row);print(c['call_id'],audited['status'],'v2',original['status'],flush=True)
 write(ROOT/'e2_results/grades_all.json',results)
if __name__=='__main__':main()
