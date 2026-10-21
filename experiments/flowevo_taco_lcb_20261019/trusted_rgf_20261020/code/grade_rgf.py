"""Private hidden evaluator. Candidate receives stdin only, never expected values."""
import ast,collections,hashlib,json,pathlib,re,sys
from decimal import Decimal,InvalidOperation
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from sandbox import Worker
from adapter import evaluate_v2
from regrade import write
from suite import accepts

def extract(text):
 # Preserve historical extraction behavior: truncated/unclosed blocks are not silently repaired.
 matches=re.findall(r'```(?:python|py)?\s*\n(.*?)```',text,re.S|re.I)
 if matches:return matches[-1].strip()+'\n'
 if '```' in text:return text.strip()+'\n'
 return text.strip()+'\n' if text.strip() else ''
def evaluate(code,tid):
 source=code.read_text()
 if not source.strip():return {'status':'NO_COMPLETE_CODE','passed':False}
 try:ast.parse(source)
 except SyntaxError as exc:return {'status':'COMPILE_ERROR','passed':False,'error':str(exc)}
 cases=json.loads((ROOT/'rgf_frozen/hidden'/(tid+'.json')).read_text());count=0
 with Worker(code) as w:
  v=w.call({'mode':'compile_stdio','timeout':6})
  if v['status']!='OK':return {'status':v['status'],'passed':False,'diagnostic':v}
  for c in cases:
   v=w.call({'mode':'stdio','input':c['input'],'timeout':4 if tid.startswith('taco') else 6})
   if v['status']!='OK':return {'status':v['status'],'passed':False,'private_failed_index':c['index'],'diagnostic':v,'tests_passed':count,'total_tests':len(cases)}
   if not accepts(tid,c,v['output']):return {'status':'WRONG_ANSWER','passed':False,'private_failed_index':c['index'],'actual_preview':v['output'][:1000],'tests_passed':count,'total_tests':len(cases)}
   count+=1
 return {'status':'PASS','passed':True,'tests_passed':count,'total_tests':len(cases)}

def main():
 calls=json.loads((ROOT/'rgf_frozen/calls.json').read_text());results=[]
 for c in calls:
  dest=ROOT/'rgf_results/grades'/(c['call_id']+'.json');response=ROOT/'rgf_results/responses'/(c['call_id']+'.json')
  if not response.exists():continue
  if dest.exists():results.append(json.loads(dest.read_text()));continue
  raw=json.loads(response.read_text());text=raw['choices'][0]['message'].get('content') or '';code=ROOT/'rgf_results/programs'/(c['call_id']+'.py');code.parent.mkdir(parents=True,exist_ok=True);code.write_text(extract(text));audited=evaluate(code,c['task_id'])
  row={'call_id':c['call_id'],'task_id':c['task_id'],'condition':c['condition'],'repeat':c['repeat'],'audited_hidden':audited,'code_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'usage':raw.get('usage'),'model':raw.get('model'),'finish_reason':raw['choices'][0].get('finish_reason')}
  write(dest,row);results.append(row);print(c['call_id'],audited['status'],'tested',audited.get('tests_passed',0),flush=True)
 write(ROOT/'rgf_results/grades_all.json',results)
if __name__=='__main__':main()
