"""Supplementary legal boundary epoch; never modifies the pinned first replay."""
import hashlib,json,math,pathlib,sys
from legal_suite import R,B,accepts
from input_audit import audit
from replay import evaluate,read,write,sha
def build():
 suite={}
 def add(tid,inp,expected,method,kind='tokens',meta=None):
  suite.setdefault(tid,[]).append({'input':inp,'expected':str(expected),'comparison':kind,'meta':meta or {},'contract_scope':'LEGAL_STATEMENT_DOMAIN','provenance':'supplementary analytic boundary, no hidden test used','oracle_method':method})
 base=read(R/'public_suite.json')['cases']
 multi={'taco_0357','taco_0403','taco_0702','taco_0303','taco_0457','taco_0318','taco_0511','taco_0915','taco_0121','taco_0313','taco_0646','taco_0777','taco_0193','taco_0966','taco_0429','taco_0838','taco_0721'}
 for tid in multi:
  # Only scalar/token tasks; semantic multi-case construction has its own checker.
  if tid not in base or base[tid][0]['comparison'] in ['prior','bamboo']:continue
  chunk=base[tid][:2];inp='2\n'+''.join(c['input'].split('\n',1)[1] for c in chunk);expected='\n'.join(str(c['expected']) for c in chunk)
  add(tid,inp,expected,'concatenation of two independently solved legal cases',base[tid][0]['comparison'])
 for n in [1,100000]:
  add('taco_0543',str(n)+'\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),n-1,'deterministic chain length','float')
 n=300000;add('taco_0572',str(n)+'\n'+'1 '+'0 '*(n-2)+'2\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),n-1,'all cuts separate the only red and blue endpoints')
 for n in [634,1000]:add('taco_0403','1\n'+str(n)+'\n'+' '.join(str(2*i) for i in range(1,n+1))+'\n',n+1,'pigeonhole excludes d<n; even d=n collides; odd d=n+1 is coprime to 2')
 for n in [2000,2001]:
  counts=[(math.comb(n-1,i),i+1) for i in range(n)];counts.sort(reverse=True)
  for k in [1,2]:
   value,node=counts[k-1];add('taco_0303',f'1\n{n} {k}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),f'{node} {value%1000000007}','path root order count is binomial(n-1,root-1), exact ranking before modulo')
 n=100000;edges=[(i-1,i) for i in range(1,n)];add('taco_0702','1\n'+str(n)+'\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges),0,'input is already a path','bamboo',{'n':n,'edges':edges})
 n=200000;add('taco_0284',str(n)+'\n'+'a\n'*(n//2)+'b\n'*(n//2),2,'two disjoint letter equivalence classes')
 add('taco_0533','200000 0\n','1\n200000','complete graph is connected')
 n=15000;add('taco_0730',str(n)+'\n'+''.join(f'{i} {i+n}\n' for i in range(1,n+1)),'2 2','all nontrivial components are isolated matching pairs')
 n=200000;qs=[1,n//2,n-1];add('taco_0917',f'{n} {n}\n'+''.join(str(n-i)+'\n' for i in range(1,n+1))+str(len(qs))+'\n'+'\n'.join(map(str,qs))+'\n','\n'.join(str(pow(2,n-i-1,1000000007)) for i in qs),'complete forward DAG: choose any intermediate subset')
 n=100000;add('taco_0966',f'1\n{n}\n'+'0 '*n+'\n1000000000\n',n*n,'all ordered pairs, including equal indices, satisfy XOR mask')
 add('taco_0193','1\n1 100000\n',30000,'each decade has exactly three allowed final digits')
 add('taco_0357','2\n1\n1000000000\n2\n1000000000 999999999\n','1\n2','one note per employee is attainable and necessary')
 lo=999999900;hi=1000000000;primes=[x for x in range(lo,hi+1) if all(x%d for d in range(2,math.isqrt(x)+1))];add('taco_0646',f'1\n{lo} {hi}\n','\n'.join(map(str,primes)),'trial divisibility up to sqrt at maximum interval endpoint')
 n=100000;add('taco_0511',f'1\n{n} 1\n'+' '.join(map(str,range(n)))+'\n1\n','Garry','forced alternating single disc moves; largest distinct power belongs to second player')
 n=2000;a=list(range(n));ops=[(1,10**8),(n,0),(n//2,999)]
 total=0
 for idx,target in ops:
  i=idx-1;old=a[:];a[i]=target
  for j in range(i+1,n):a[j]=max(a[j],a[j-1]+1)
  for j in range(i-1,-1,-1):a[j]=min(a[j],a[j+1]-1)
  total+=sum(abs(x-y) for x,y in zip(old,a))
 add('lcb_atcoder_abc371_f',str(n)+'\n'+' '.join(map(str,range(n)))+'\n3\n'+'\n'.join(f'{i} {g}' for i,g in ops)+'\n',total,'order-preserving nearest feasible propagation; large coordinate overflow check')
 for tid,cases in suite.items():
  for c in cases:audit(tid,c['input'])
 return suite
def main():
 suite=build();write(R/'stress_suite_v2.json',{'role':'supplementary_boundary_epoch','new_model_calls':0,'cases':suite})
 frozen={'suite_sha256':sha(R/'stress_suite_v2.json'),'code_sha256':sha(pathlib.Path(__file__)),'sampling_manifest_sha256':sha(R/'review_manifest.json')}
 dest=R/'stress_frozen_v2.json'
 if dest.exists():assert read(dest)==frozen
 else:write(dest,frozen)
 m=read(R/'review_manifest.json');executions=0;programs=0
 for t in m['tasks']:
  tid=t['task_id']
  if tid not in suite:continue
  task=read(R/'source/tasks'/(tid+'.json'))
  for a in t['historical_programs']:
   p=R/a['source_path'];out=R/'stress_verdicts_v2'/tid/(a['stage']+'.json')
   if out.exists():v=read(out)
   else:
    v=evaluate(tid,p,suite[tid],task.get('function_name'));v.update(task_id=tid,stage=a['stage'],code_sha256=a['code_sha256']);write(out,v);print('BOUNDARY',tid,a['stage'],v['status'],v['tests_passed'],flush=True)
   executions+=v['executions'];programs+=1
 write(R/'stress_summary_v2.json',{'tasks':len(suite),'cases':sum(map(len,suite.values())),'programs':programs,'sandbox_test_executions':executions,'new_model_calls':0})
if __name__=='__main__':main()
