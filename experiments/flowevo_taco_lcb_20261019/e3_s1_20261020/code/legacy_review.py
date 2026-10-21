"""Case-scoped legacy failure audit. Private old inputs never enter public generators."""
import collections,functools,itertools,json,math,pathlib,sys
from legal_suite import R,B,graph_components,playlist,tree_orders,min_bamboo,accepts
from input_audit import audit,Cursor
from replay import evaluate,read,write,sha
def normalize(inp,fn):
 if not fn and isinstance(inp,list) and all(isinstance(x,str) for x in inp):return '\n'.join(inp)+'\n'
 return inp
def reference(tid,inp):
 s=Cursor(inp);out=[];method='independent statement-derived direct calculation';semantic=[]
 if tid in ['taco_0711','taco_0284','taco_0533','taco_0730','taco_0995']:
  if tid=='taco_0711':
   n,m=s.num(),s.num();a=s.nums(n);edges=[(s.num()-1,s.num()-1) for _ in range(m)];parts=graph_components(n,edges);out=[math.prod(sum(a[v]==max(a[u] for u in part) for v in part) for part in parts)%1000000007];method='connected components and direct count of maximal-knowledge members'
  elif tid=='taco_0284':
   n=s.num();ss=[set(s.take()) for _ in range(n)]
   if n>1000:raise NotImplementedError('oracle size bound')
   out=[len(graph_components(n,[(i,j) for i in range(n) for j in range(i) if ss[i]&ss[j]]))]
  elif tid=='taco_0533':
   n,m=s.num(),s.num();missing={tuple(sorted((s.num()-1,s.num()-1))) for _ in range(m)}
   if n>1000:raise NotImplementedError('oracle size bound')
   parts=graph_components(n,[e for e in itertools.combinations(range(n),2) if e not in missing]);out=[len(parts)]+sorted(map(len,parts))
  elif tid=='taco_0730':
   m=s.num();edges=[(s.num()-1,s.num()-1) for _ in range(m)];n=max(max(e) for e in edges)+1;parts=[p for p in graph_components(n,edges) if len(p)>1];out=[min(map(len,parts)),max(map(len,parts))]
  else:
   n=s.num();a=[s.nums(n) for _ in range(n)];q=s.num();ans=[]
   if n*n*q>10000000:raise NotImplementedError('oracle size bound')
   for _ in range(q):
    typ=s.num()
    if typ==1:i=s.num()-1;a[i]=[1-x for x in a[i]]
    elif typ==2:
     i=s.num()-1
     for row in a:row[i]=1-row[i]
    else:ans.append(str(sum(a[i][j]*a[j][i] for i in range(n) for j in range(n))%2))
   out=[''.join(ans)]
 else:
  t=s.num()
  for _ in range(t):
   if tid=='taco_0838':
    text=s.take();z=10**30
    for perm in itertools.permutations('rgb'):
     count=collections.Counter();cost=0;rank={v:i for i,v in enumerate(perm)}
     for ch in text:cost+=sum(v for c,v in count.items() if rank[c]>rank[ch]);count[ch]+=1
     z=min(z,cost)
    out.append(z);method='all six grouped color orders; exact inversion count equals minimum adjacent-move distance'
   elif tid=='taco_0457':
    m,n,p,q=s.num(),s.num(),s.num(),s.num();m-=p;n-=q
    if m*n>20000 or max(m,n)>150:raise NotImplementedError('oracle size bound')
    win=[[False]*(n+1) for _ in range(m+1)]
    for i in range(m+1):
     for j in range(n+1):win[i][j]=any(not win[k][j] for k in range(i)) or any(not win[i][k] for k in range(j)) or any(not win[i-d][j-d] for d in range(1,min(i,j)+1))
    out.append('Alice' if win[m][n] else 'Bob');method='exhaustive finite normal-play game-state DP from legal moves'
   elif tid=='taco_0318':
    n=s.num();a=s.nums(n);possible=[]
    for x in a:
     row=[]
     while x:
      if x<=n:row.append(x)
      x//=2
     possible.append(row)
    assigned={}
    def augment(i,seen):
     for v in possible[i]:
      if v in seen:continue
      seen.add(v)
      if v not in assigned or augment(assigned[v],seen):assigned[v]=i;return True
     return False
    out.append('YES' if all(augment(i,set()) for i in range(n)) else 'NO');method='exact bipartite perfect matching of all reachable halved values'
   elif tid=='taco_0511':
    n,k=s.num(),s.num();a=s.nums(n);moves=s.nums(k)
    if n>14 or max(a)>500:raise NotImplementedError('minimax oracle size bound')
    @functools.lru_cache(None)
    def best(i):return 0 if i==n else max(sum(2**v for v in a[i:i+k])-best(i+k) for k in moves if i+k<=n)
    z=best(0);out.append('Chef' if z>0 else 'Garry' if z<0 else 'Draw');method='exact score-difference minimax of all legal pop sizes'
   elif tid=='taco_0915':
    n,q=s.num(),s.num();a=s.nums(n)
    if n*q>1000000:raise NotImplementedError('oracle size bound')
    for _ in range(q):l,r,k=s.num(),s.num(),s.num();out.append(sum(len(list(g))>=k for v,g in itertools.groupby(a[l-1:r])))
    method='directly enumerate maximal equal-price runs in each queried slice'
   elif tid=='taco_0121':
    n,k=s.num(),s.num();a=s.nums(n);out.append(sum(a.count(i)>=k and a[i-1]!=i for i in range(1,n+1)));method='direct vote counts with self-voter disqualification'
   elif tid=='taco_0313':
    n=s.num();a=s.nums(n)
    if n>2000:raise NotImplementedError('oracle size bound')
    out.extend(playlist(a));method='literal song-by-song simulation with memory reset after each deletion'
   elif tid=='taco_0303':
    n,k=s.num(),s.num();edges=[(s.num()-1,s.num()-1) for _ in range(n-1)]
    if n>8:raise NotImplementedError('factorial oracle size bound')
    rank=sorted((v,i+1) for i,v in enumerate(tree_orders(n,edges)));z,u=rank[-k];out.extend([u,z]);method='enumerate all vertex permutations and validate child-before-parent for each root'
   elif tid=='taco_0646':
    lo,hi=s.num(),s.num()
    if hi-lo>10000 or hi>1000000:raise NotImplementedError('trial-division oracle size bound')
    out.extend(x for x in range(lo,hi+1) if x>=2 and all(x%d for d in range(2,math.isqrt(x)+1)));method='trial divisibility through integer sqrt; preserve ordered prime list'
   elif tid=='taco_0777':
    n,h=s.num(),s.num();gaps=[(s.num(),s.num()) for _ in range(n)]
    if n*n*h>2000000:raise NotImplementedError('oracle size bound')
    out.append(min(sum(not lo<=row<=hi for lo,hi in gaps for row in range(start,start+h)) for start in range(n-h+1)));method='enumerate every legal horizontal corridor and count soil cells'
   elif tid=='taco_0193':
    lo,hi=s.num(),s.num();out.append(sum(x%10 in [2,3,9] for x in range(lo,hi+1)));method='enumerate every integer in the inclusive legal interval'
   elif tid=='taco_0702':
    n=s.num();edges=[(s.num()-1,s.num()-1) for _ in range(n-1)]
    if n>14:raise NotImplementedError('edge-subset oracle size bound')
    semantic.append({'input':'','expected':str(min_bamboo(n,edges)),'comparison':'bamboo','meta':{'n':n,'edges':edges}});method='exhaustive original-edge subset maximum degree-two forest plus operation-by-operation graph checking'
   else:raise NotImplementedError('independent raw reference not implemented')
 s.done();return {'expected':'\n'.join(map(str,out)),'comparison':'bamboo_batch' if semantic else 'tokens','semantic_cases':semantic,'method':method}
def compare(tid,ref,actual):
 if ref['comparison']!='bamboo_batch':return str(actual).split()==str(ref['expected']).split()
 try:
  vals=str(actual).split();i=0
  for c in ref['semantic_cases']:
   k=int(vals[i]);n=c['meta']['n']
   if not 0<=k<n:return False
   take=1+4*k
   if not accepts(tid,c,' '.join(vals[i:i+take])):return False
   i+=take
  return i==len(vals)
 except (ValueError,IndexError):return False
def main():
 manifest=read(R/'review_manifest.json');all_rows=read(R/'source/candidate_results.json');by={(x['task_id'],x['stage']):x for x in all_rows};prior=read(R/'input_contract_review.json');audits={x['task_id']:x for x in prior};extended=[];evidence=[]
 for t in manifest['tasks']:
  tid=t['task_id'];task=read(R/'source/tasks'/(tid+'.json'));io=task['input_output'];io=json.loads(io) if isinstance(io,str) else io;fn=task.get('function_name');findings=[];checked=0;unknown=0
  for i,raw in enumerate(io['inputs']):
   inp=normalize(raw,fn)
   try:audit(tid,inp);checked+=1
   except NotImplementedError:unknown+=1
   except (ValueError,TypeError,IndexError) as exc:checked+=1;findings.append({'case_index':i,'finding':str(exc)})
  extended.append({'task_id':tid,'legacy_cases_total':len(io['inputs']),'checked':checked,'unknown':unknown,'invalid':len(findings),'findings':findings,'line_list_serialization_normalized':not fn and any(isinstance(x,list) for x in io['inputs'])})
  invalid={x['case_index']:x for x in findings}
  for a in t['historical_programs']:
   old=by[tid,a['stage']];i=old.get('failed_test_index')
   if i is None:continue
   mapping=old['total_tests']==len(io['inputs']) and old['valid_tests']==old['total_tests'] and old['reference_corrections']==0
   packet={'task_id':tid,'stage':a['stage'],'code_sha256':a['code_sha256'],'regrade_epoch':old['epoch'],'regraded_status':old['status'],'raw_index':i,'raw_index_mapping_confirmed':mapping,'scope':'exact historical candidate and old raw case only','classification':'ROOT_CAUSE_UNKNOWN'}
   if not mapping:packet['reason']='filtered/corrected legacy suite; raw index mapping not assumed';evidence.append(packet);continue
   raw=io['inputs'][i];inp=normalize(raw,fn);expected=io['outputs'][i];expected='\n'.join(map(str,expected)) if not fn and isinstance(expected,list) else expected
   packet.update(raw_input=raw,normalized_input=inp,legacy_expected=expected)
   if i in invalid:packet.update(classification='VERIFIED_EVALUATION_PROBLEM',subtype='invalid_test_input',independent_contract_finding=invalid[i]['finding']);evidence.append(packet);continue
   if fn:packet['reason']='function-specific legacy diagnosis retained in prior audit';evidence.append(packet);continue
   try:
    audit(tid,inp);ref=reference(tid,inp);packet['independent_reference']=ref
    if not compare(tid,ref,expected):packet.update(classification='VERIFIED_EVALUATION_PROBLEM',subtype='invalid_reference_or_cardinality')
    elif ref['comparison']=='bamboo_batch':packet.update(classification='VERIFIED_EVALUATION_PROBLEM',subtype='strict_text_comparison_of_multiple_valid_constructions')
    code=R/a['source_path'];dest=R/'legacy_execution'/tid/(a['stage']+'.json')
    if dest.exists():actual=read(dest)
    elif ref['comparison']=='bamboo_batch':
     from replay import Worker
     with Worker(code) as w:w.call({'mode':'compile_stdio','timeout':6});actual=w.call({'mode':'stdio','input':inp,'timeout':4})
     write(dest,actual)
    else:
     v=evaluate(tid,code,[{'input':inp,'expected':ref['expected'],'comparison':'tokens'}]);actual=v;write(dest,actual)
    packet['independent_case_execution']=actual
    if ref['comparison']=='bamboo_batch' and not (actual['status']=='OK' and compare(tid,ref,actual.get('output',''))):packet['classification']='ROOT_CAUSE_UNKNOWN';packet['reason']='candidate construction not independently accepted'
    elif ref['comparison']!='bamboo_batch' and not actual.get('passed'):packet['classification']='ROOT_CAUSE_UNKNOWN';packet['reason']='candidate does not pass independent raw oracle; further semantic review required'
   except NotImplementedError as exc:packet['reason']=str(exc)
   except (ValueError,IndexError,TypeError) as exc:packet['reason']='unresolved raw contract/reference: '+str(exc)
   evidence.append(packet)
 write(R/'input_contract_review_extended.json',extended);write(R/'legacy_failure_evidence.json',evidence)
 print('LEGACY',collections.Counter(x['classification'] for x in evidence),'invalid',sum(x['invalid'] for x in extended),flush=True)
if __name__=='__main__':main()
