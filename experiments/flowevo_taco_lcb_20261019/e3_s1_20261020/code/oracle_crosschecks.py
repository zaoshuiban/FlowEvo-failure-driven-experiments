"""Independent bounded cross-checks for new statement-derived oracles/checkers."""
import collections,itertools,json,math,random
from legal_suite import R,graph_components,min_bamboo,tree_orders,accepts,playlist
def main():
 checks=collections.Counter();rng=random.Random(20261022)
 # Global Hamiltonian-path enumeration is independent of the edge-subset oracle.
 for n in range(2,7):
  for rep in range(12):
   edges=[(rng.randrange(v),v) for v in range(1,n)];original={tuple(sorted(e)) for e in edges}
   best=min(n-1-len(original&{tuple(sorted(e)) for e in zip(p,p[1:])}) for p in itertools.permutations(range(n)))
   assert best==min_bamboo(n,edges);checks['bamboo_subset_vs_global_path']+=1
   c={'comparison':'bamboo','expected':best,'meta':{'n':n,'edges':edges}}
   assert not accepts('taco_0702',c,'1\n1 1 1 1');checks['bamboo_illegal_selfloop_rejected']+=1
 for n in range(2,8):
  edges=[(i,i+1) for i in range(n-1)];actual=tree_orders(n,edges);assert actual==[math.comb(n-1,i) for i in range(n)];checks['path_rank_exact_permutations_vs_binomial']+=n
 # Multi-source BFS over literal adjacent swaps; no inversion formula used.
 public=json.loads((R/'public_suite.json').read_text())['cases'];distance={}
 for n in range(1,7):
  for r in range(n+1):
   for g in range(n-r+1):
    blocks={'r':'r'*r,'g':'g'*g,'b':'b'*(n-r-g)};starts={''.join(blocks[c] for c in p) for p in itertools.permutations('rgb')};q=collections.deque(starts);seen={s:0 for s in starts}
    while q:
     text=q.popleft()
     for i in range(n-1):
      chars=list(text);chars[i],chars[i+1]=chars[i+1],chars[i];new=''.join(chars)
      if new not in seen:seen[new]=seen[text]+1;q.append(new)
    distance.update(seen)
 for c in public['taco_0838']:
  text=c['input'].split()[1]
  if text in distance:assert int(c['expected'])==distance[text];checks['containers_inversions_vs_adjacent_swap_BFS']+=1
 # Pair multiplicity must retain order and equal-index pairs.
 for _ in range(100):
  a=[rng.randrange(32) for _ in range(rng.randint(1,12))];x=rng.randrange(32);count=collections.Counter(v&x for v in a)
  assert sum(v*v for v in count.values())==sum(((u^v)&x)==0 for u in a for v in a);checks['ordered_pair_enumeration_vs_frequency']+=1
 # Exhaustive reachability and reading order for small DAGs, using transitive closure.
 for _ in range(20):
  n=5;order=list(range(n));rng.shuffle(order)
  if order[0]==0:order[0],order[-1]=order[-1],order[0]
  deps=[[] for _ in range(n)]
  for i in range(n):deps[order[i]]=[order[j] for j in range(i) if rng.random()<.4]
  if not deps[0]:deps[0]=[order[0]]
  reach=[[False]*n for _ in range(n)]
  for i,row in enumerate(deps):
   for j in row:reach[i][j]=True
  for k in range(n):
   for i in range(n):
    for j in range(n):reach[i][j]|=reach[i][k] and reach[k][j]
  needed={i for i in range(1,n) if reach[0][i]};c={'comparison':'topological','meta':{'deps':deps}}
  for permutation in itertools.permutations(needed):
   pos={x:i for i,x in enumerate(permutation)};valid=all(pos[j]<pos[i] for i in needed for j in deps[i]);assert accepts('lcb_atcoder_abc315_e',c,' '.join(str(x+1) for x in permutation))==valid;checks['topological_checker_vs_transitive_closure']+=1
  assert not accepts('lcb_atcoder_abc315_e',c,' '.join(str(x+1) for x in needed)+' 1');checks['unnecessary_root_rejected']+=1
 # Statement's playlist examples, including deleting a lone 1 and retaining a lone 2.
 for a,expected in [([5,9,2,10,15],[2,2,3]),([1,2,4,2,4,2],[2,2,1]),([1,2],[2,2,1]),([1],[1,1]),([2],[0])]:assert playlist(a)==expected;checks['playlist_statement_examples']+=1
 assert not accepts('taco_0966',{'comparison':'tokens','expected':'1\n1'},'1');checks['ordered_output_multiplicity_preserved']+=1
 assert accepts('taco_0543',{'comparison':'float','expected':'0'},'0.000000000000000');checks['float_stress_false_positive_prevented']+=1
 out={'status':'PASS','checks':dict(checks),'total_crosschecks':sum(checks.values()),'scope':'bounded independent checks; not proof of full-domain correctness','new_model_calls':0}
 (R/'oracle_crosschecks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
