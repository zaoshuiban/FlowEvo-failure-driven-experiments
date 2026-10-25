import json,pathlib,re,hashlib
import pyarrow.parquet as pq
P=pathlib.Path(__file__).parent;raw=pathlib.Path('/Users/majiatong/lab/AFlow/results/experiment_d0_20261019_s0_v1/data/taco_ALL_test-00000-of-00001.parquet')
rows=[]
for b in pq.ParquetFile(raw).iter_batches(batch_size=32,columns=['question','url']):rows.extend(b.to_pylist())
def grams(s):
 t=re.findall(r'[a-z0-9]+',s.lower());return set(zip(t,t[1:],t[2:],t[3:],t[4:]))
def url(s):
 s=str(s).rstrip('/');s=re.sub(r'/contest/(\d+)/problem/','/problemset/problem/\\1/',s);return s.replace('http://','https://').replace('www.','')
ex=set(map(int,json.loads((P/'exposure.json').read_text())));c=json.loads((P/'candidate_order.json').read_text()); gs=[grams(t['question']) for t in rows];out=[]
for x in c:
 i=int(x['id'].split('-')[-1]);best=(0,None);same=[]
 for j in sorted(ex|{int(y['id'].split('-')[-1]) for y in c if y['rank']<x['rank']}):
  if j==i:continue
  score=len(gs[i]&gs[j])/max(1,len(gs[i]|gs[j]))
  if score>best[0]:best=(score,j)
  if url(rows[i]['url'])==url(rows[j]['url']):same.append(j)
 out.append({'id':x['id'],'max_5gram_jaccard':best[0],'nearest_source_index':best[1],'same_canonical_url':same,'pass':best[0]<.85 and not same})
(P/'near_duplicate_audit.json').write_text(json.dumps({'threshold':.85,'method':'lowercase alphanumeric statement 5grams Jaccard; canonical Codeforces original identity; against all excluded and candidate peers; metadata-only, no model output','results':out},indent=2));print('near duplicates',sum(not x['pass'] for x in out))
