import datetime,hashlib,json,pathlib,random,sys
from suite import ROOT,BASE,additions
from replay import evaluate
sys.path.insert(0,str(BASE/'e1_e2_20261020/code'))
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'));from regrade import write

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if (ROOT/'rgf_frozen/manifest.json').exists():print('Already frozen');return
 v=json.loads((ROOT/'validation.json').read_text());assert v['accepted_tasks']==35
 contracts=json.loads((ROOT/'input_contract_review.json').read_text());assert len(contracts)==35
 catalog={c['task_id']:c for c in json.loads((BASE/'repair_v2_20261020/catalog.json').read_text())};ids=['lcb_atcoder_abc301_f','taco_0875'];root_causes={'lcb_atcoder_abc301_f':{'family':'alphabet_combinatorics_table_capacity','mechanism':'A combinatorial table is sized using the length of the current input, but later indices also range over a fixed alphabet of 26 symbols. Legal short inputs can therefore request an unallocated index. Allocate for every reachable index, not just the input-length variable.','minimal_counterfactual':'Increase only the factorial and inverse-factorial precomputation capacity to at least 26; preserve the DP and transitions.'},'taco_0875':{'family':'memoized_tree_depth_recursion_resource','mechanism':'Memoization reduces repeated work but does not reduce the maximum depth of recursive calls. A legal deep chain can exceed the language runtime recursion limit before producing an answer. Distinguish graph cycles from a long acyclic chain.','minimal_counterfactual':'Raise the recursion limit above the stated maximum chain length or implement the same depth recurrence iteratively.'}}
 bank=[];calls=[];hidden_all=additions(20261023)
 for tid in ids:
  verdict=json.loads((ROOT/'verdicts'/tid/'l1.json').read_text());patch=json.loads((ROOT/'counterfactuals'/tid/'verification.json').read_text());assert verdict['status']=='RUNTIME_ERROR' and patch['passed']
  witness=verdict['case'];public={'input':witness['input'],'expected':witness['expected'],'exception_class':'IndexError' if tid.startswith('lcb') else 'RecursionError','source':'independent public statement-domain generator, no benchmark hidden input'}
  hidden=[c for c in hidden_all[tid] if c['input']!=public['input']];assert hidden
  from contracts_audit import audit
  for i,case in enumerate(hidden):case['index']=i;audit(tid,case)
  oldpath=next(BASE.glob('runs/*/'+tid+'/l1.py'));fixed=ROOT/'counterfactuals'/tid/'fixed.py';original=evaluate(tid,oldpath,hidden);corrected=evaluate(tid,fixed,hidden);assert not original['passed'] and corrected['passed'],tid
  write(ROOT/'rgf_frozen/hidden'/(tid+'.json'),hidden);write(ROOT/'rgf_frozen/baselines'/(tid+'.json'),{'original':original,'counterfactual':corrected,'public':public})
  bank.append({'task_id':tid,'original_stage':'l1','code_sha256':sha(oldpath),'root_cause':root_causes[tid],'public_evidence':public,'minimal_patch':str((ROOT/'counterfactuals'/tid/'minimal.diff').relative_to(ROOT)),'verified_actual_failure':True,'synthetic_mutant':False})
 write(ROOT/'failure_mechanism_bank.json',bank)
 for tid in ids:
  oldpath=next(BASE.glob('runs/*/'+tid+'/l1.py'));source=oldpath.read_text();meta=catalog[tid];public=json.loads((ROOT/'rgf_frozen/baselines'/(tid+'.json')).read_text())['public'];train=[x for x in bank if x['task_id']!=tid and x['root_cause']['family']!=root_causes[tid]['family']];assert train
  common='Solve the following Python 3.10 competitive programming repair task. Preserve correct existing logic where possible. Return the complete corrected program in one closed Python code block.\n\nProblem:\n'+meta['prompt']+'\n\nFrozen historical candidate source (JSON string):\n'+json.dumps(source)+'\n\nPublic diagnostic, identical in every condition:\n'+json.dumps(public)+'\n\n'
  guidance={'R':'Reflection: reflect on why the candidate fails this legal public diagnostic, identify the underlying cause, then repair it. Think about whether your explanation predicts the observed failure.','G':'Generic repair: check the input contract, indexing bounds, initialization, control flow, runtime resources and complexity. Make a correct, efficient repair and return the complete program.','F':'Failure-mechanism-guided repair: consider the following verified mechanism from OTHER tasks, apply it only if relevant, and then repair the candidate. Do not blindly copy an unrelated fix.\n'+json.dumps([{'source_task':x['task_id'],'mechanism':x['root_cause']['mechanism']} for x in train])}
  for condition in ['R','G','F']:
   body={'model':'deepseek-reasoner','messages':[{'role':'system','content':'You are an expert competitive programmer. Produce a correct and efficient Python solution.'},{'role':'user','content':common+guidance[condition]}],'temperature':0.2,'max_tokens':32768,'thinking':{'type':'enabled'},'reasoning_effort':'high'}
   for repeat in [1,2]:calls.append({'task_id':tid,'condition':condition,'repeat':repeat,'request':body,'expected_actual_model':'deepseek-flash','source_sha256':sha(oldpath),'public_witness':public,'failure_memory_source_tasks':[x['task_id'] for x in train] if condition=='F' else [],'own_task_root_cause_disclosed':False})
 random.Random(20261024).shuffle(calls)
 for i,c in enumerate(calls):c['call_id']=f'{i+1:02d}_{c["task_id"]}_{c["condition"]}_{c["repeat"]}'
 write(ROOT/'rgf_frozen/calls.json',calls)
 files=list((ROOT/'code').glob('*.py'))+[ROOT/'suite_frozen.json',ROOT/'trusted_tasks.json',ROOT/'validation.json',ROOT/'input_contract_review.json',ROOT/'failure_mechanism_bank.json',ROOT/'协议.md']+list((ROOT/'rgf_frozen').rglob('*.json'))
 files+=list((BASE/'repair_v2d_20261020/code').glob('*.py'))+[BASE/'e1_e2_20261020/code/e2_oracles.py']
 hashes={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(BASE)):sha(p) for p in files if not p.name.startswith('._')}
 write(ROOT/'rgf_frozen/manifest.json',{'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trusted_tasks':35,'independent_failure_tasks':2,'planned_calls':12,'max_calls':72,'max_total_tokens':3000000,'history_inventory':2132,'offline_replayed_programs':155,'F_leave_one_task_and_family_out':True,'no_synthetic_training_failures':True,'same_public_diagnostics_across_arms':True,'hashes':hashes,'scope':'exploratory implementation-failure repair; no demonstrated algorithm-choice or transition failures; independent task n=2'})
 print('Frozen R/G/F: tasks',len(ids),'calls',len(calls))
if __name__=='__main__':main()
