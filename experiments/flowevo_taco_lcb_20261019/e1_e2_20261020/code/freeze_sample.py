"""Prompt-only family stratification. No candidate programs are read here."""
import collections,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]; BASE=ROOT.parent/'repair_v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def family(prompt):
    # Ordered, overlapping keyword families; labels are descriptive rather than algorithm truth.
    rules=[('graph_tree',r'\b(graph|tree|vertices|vertex|edges|shortest path)\b'),('geometry_grid',r'\b(grid|matrix|rectangle|coordinates|polygon|circle|chessboard)\b'),('strings',r'\b(string|substring|subsequence|palindrome|characters)\b'),('permutation_combinatorics',r'\b(permutation|permutations|combinations|modulo|998244353|1000000007)\b'),('number_theory',r'\b(prime|divisor|divisors|gcd|lcm|divisible)\b'),('sequence_query',r'\b(array|sequence|queries|interval|subarray|integers)\b')]
    return next((n for n,p in rules if re.search(p,prompt,re.I)),'arithmetic_simulation_other')
def rank(t):return sha(('20261020:'+t['task_id']).encode())
def allocate(rows,n):
    groups=collections.defaultdict(list)
    for x in rows:groups[(x['dataset'],x['difficulty'],x['family'])].append(x)
    quotas={k:len(v)*n//len(rows) for k,v in groups.items()}
    rest=n-sum(quotas.values())
    order=sorted(groups,key=lambda k:(-(len(groups[k])*n%len(rows)),k))
    for k in order[:rest]:quotas[k]+=1
    selected=[]
    for k in sorted(groups):
        selected+=sorted(groups[k],key=rank)[:quotas[k]]
    return selected,[{'stratum':list(k),'population':len(groups[k]),'sample':quotas[k]} for k in sorted(groups)]
def main():
    catalog={x['task_id']:x for x in json.loads((BASE/'catalog.json').read_text())}
    rows=json.loads((BASE/'epochs/repaired_reports_20261020/task_results.json').read_text())
    for x in rows:x['family']=family(catalog[x['task_id']]['prompt'])
    pools={'persistent_wa':([x for x in rows if not x['old_final_pass'] and x['reported_final_status']=='WRONG_ANSWER'],50),'exceptions':([x for x in rows if x['reported_final_status'] in ['RUNTIME_ERROR','COMPILE_ERROR','TIME_LIMIT']],5),'rescued_pass':([x for x in rows if not x['old_final_pass'] and x['reported_final_status']=='PASS'],20),'regressed_wa':([x for x in rows if x['old_final_pass'] and x['reported_final_status']=='WRONG_ANSWER'],18)}
    selected=[];frames={}
    for name,(pool,n) in pools.items():
        pick,quotas=allocate(pool,n)
        for x in pick:x['sampling_group']=name
        selected+=pick;frames[name]={'population':len(pool),'target':n,'quotas':quotas,'frame_ids':sorted(x['task_id'] for x in pool)}
    assert len(selected)==93 and len({x['task_id'] for x in selected})==93
    result={'seed':20261020,'family_rule':'ordered prompt keyword labels, not inferred algorithm or code inspection','allocation':'largest remainder; tied strata lexicographic; SHA256(seed:task_id) within stratum; zero quotas allowed for small strata, no post hoc merging','source_hashes':{str(p.relative_to(BASE)):sha(p.read_bytes()) for p in [BASE/'catalog.json',BASE/'epochs/repaired_reports_20261020/task_results.json']},'frames':frames,'selected':sorted(selected,key=lambda x:(x['sampling_group'],rank(x)))}
    path=ROOT/'sample_frozen.json';payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if path.exists():assert path.read_text()==payload,'Frozen sample cannot change'
    else:path.write_text(payload)
    (ROOT/'sample_frozen.sha256').write_text(sha(payload.encode())+'\n')
    for name in pools:print(name,[(x['task_id'],x['difficulty'],x['family']) for x in result['selected'] if x['sampling_group']==name])
if __name__=='__main__':main()
