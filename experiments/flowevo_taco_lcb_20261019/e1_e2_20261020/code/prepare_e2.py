import ast,copy,hashlib,json,pathlib,random,sys
from decimal import Decimal
from e2_oracles import magazine,transform,selftest
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from regrade import write
PUBLIC={'taco_0291':{'input':'1\n2\n0\n0\n','expected':'3.0000','proof':'There is one intact physical leaf containing labels 1 and 2, no missing labels and no tearing; sum=3.'},'lcb_atcoder_abc399_e':{'input':'1\na\nb\n','expected':'1','proof':'One global replacement a->b suffices; zero operations cannot change a to b.'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=ROOT/'e2_frozen'
 if (dest/'manifest.json').exists():print('Already frozen');return
 tests_checked=selftest();calls=[];tasks=[]
 for tid in sorted(PUBLIC):
  oldpath=next(BASE.glob('runs/*/'+tid+'/result.json'));history=json.loads(oldpath.read_text());stage=history['final_stage'];candidate=oldpath.parent/(stage+'.py');source=candidate.read_text();responsepath=oldpath.parent/(stage+'.response.json');response=json.loads(responsepath.read_text());assert response['finish_reason']=='length' and response['usage']['completion_tokens']==32768
  try:ast.parse(source)
  except SyntaxError as err:syntax=str(err)
  else:raise AssertionError('Not a verified compile failure')
  pub=PUBLIC[tid]
  if tid.startswith('taco'):assert magazine(list(map(int,pub['input'].split())))==[3]
  else:
   ss=pub['input'].split();assert transform(ss[1],ss[2])==int(pub['expected'])
  request=response['request'];olduser=request['messages'][1]['content'];prefix=olduser.split('\n\nPrevious candidate:\n',1)[0];marker='\nFix the solution and return the corrected complete Python program/function.'
  tail=olduser.split(marker,1)[1];oldfeedback=history['attempts'][-1]['feedback']
  for condition in ['R0','R1','R2']:
   feedback=oldfeedback if condition=='R0' else 'Compilation error.'
   if condition=='R2':feedback+='\nIndependently generated PUBLIC test:\nInput:\n'+pub['input']+'Expected output:\n'+pub['expected']+'\nPublic compilation observation: the frozen candidate fails Python syntax compilation before executing this test. '+pub['proof']
   user=prefix+'\n\nFrozen previous candidate source (JSON-encoded string, including any accidental Markdown):\n'+json.dumps(source)+'\n\nVerifier feedback: '+feedback+marker+tail
   body=copy.deepcopy(request);body['messages'][1]['content']=user
   assert body['max_tokens']==32768
   for repeat in [1,2]:calls.append({'task_id':tid,'condition':condition,'repeat':repeat,'request':body,'expected_actual_model':response['model'],'source_sha256':sha(candidate),'original_request_sha256':hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest(),'public_witness':pub if condition=='R2' else None,'feedback_relation':'broad category includes correct compilation diagnosis; auxiliary specificity cohort'})
  # Hidden data stay outside request construction and candidate sandbox.
  taskpath=BASE/'data/tasks'/(tid+'.json');task=json.loads(taskpath.read_text());io=json.loads(task['input_output']);hidden=[];excluded=[];corrected=[]
  for i,(inp,provided) in enumerate(zip(io['inputs'],io['outputs'])):
   try:
    if tid.startswith('taco'):
     answers=magazine(list(map(int,inp.split())));expected=[str(Decimal(v.numerator)/Decimal(v.denominator)) for v in answers]
     tokens=str(provided).split();same=len(tokens)==len(expected) and all(abs(Decimal(a)-Decimal(b))<=Decimal('0.00005') for a,b in zip(tokens,expected))
    else:
     ss=inp.split()
     if len(ss)!=3:raise ValueError('LCB input token count')
     n=int(ss[0]);s,t=ss[1:]
     if not(1<=n<=200000 and len(s)==len(t)==n and all('a'<=c<='z' for c in s+t)):raise ValueError('LCB length/alphabet')
     expected=[str(transform(s,t))];same=str(provided).split()==expected
    hidden.append({'index':i,'input':inp,'expected':expected,'comparison':'rounded_four_decimals' if tid.startswith('taco') else 'integer_tokens'})
    if not same:corrected.append(i)
   except (ValueError,IndexError,TypeError,ArithmeticError) as exc:excluded.append({'index':i,'reason':str(exc)})
  assert hidden
  path=dest/'hidden'/(tid+'.json');write(path,hidden);write(dest/'quality'/(tid+'.json'),{'total':len(io['inputs']),'retained':len(hidden),'excluded':excluded,'reference_corrected_indices':corrected,'task_sha256':sha(taskpath),'hidden_sha256':sha(path)})
  write(dest/'checkpoints'/(tid+'.json'),{'task_id':tid,'original_stage':stage,'syntax':syntax,'old_feedback':oldfeedback,'source':source,'source_sha256':sha(candidate),'original_response_sha256':sha(responsepath)})
  tasks.append({'task_id':tid,'cohort':'implementation_completeness_auxiliary','hidden_tests':len(hidden),'excluded':len(excluded),'reference_corrected':len(corrected)})
 random.Random(20261020).shuffle(calls)
 for i,c in enumerate(calls):c['call_id']=f'{i+1:02d}_{c["task_id"]}_{c["condition"]}_{c["repeat"]}'
 write(dest/'calls.json',calls)
 manifest={'primary_algorithm_failure_cohort':0,'auxiliary_tasks':tasks,'planned_calls':len(calls),'max_calls':72,'max_total_tokens':3000000,'no_retries':True,'seed':20261020,'oracle_selftest':tests_checked,'r2_hidden_data_disclosed':False,'protocol_amendment':'E2执行补充协议.md','hashes':{str(p.relative_to(ROOT)):sha(p) for p in list((ROOT/'code').glob('*.py'))+[ROOT/'sample_frozen.json',ROOT/'e1_cards.json',ROOT/'E2执行补充协议.md']+list(dest.rglob('*.json'))}}
 write(dest/'manifest.json',manifest);print(json.dumps({'tasks':tasks,'planned_calls':len(calls),'tests':tests_checked},ensure_ascii=False))
if __name__=='__main__':main()
