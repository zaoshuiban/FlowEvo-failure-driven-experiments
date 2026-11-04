"""Read-only archive retrieval and candidate matching; never certifies provenance by similarity."""
import sys,json,re,hashlib,time,urllib.request,concurrent.futures,subprocess,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/math_stream200_provenance_gate_20261102_01'
DATA=ROOT/'datasets/math_olympiad_three_domain200_20261102'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jobs():
 out=[]
 for year in range(2000,2024):
  for month,rounds in [('nov',['gen','thm','team','guts'])] if year>=2008 else []:
   for round in rounds:out.append(dict(key=f'hmmt-{year}-{month}-{round}',url=f'https://hmmt-archive.s3.amazonaws.com/tournaments/{year}/{month}/{round}/problems.pdf',family='HMMT_11',year=year,round=round,authority='ORGANIZER_ARCHIVE'))
  for round in ['algnt' if year>=2011 else 'alg','comb','team','guts']:
   out.append(dict(key=f'hmmt-{year}-feb-{round}',url=f'https://hmmt-archive.s3.amazonaws.com/tournaments/{year}/feb/{round}/problems.pdf',family='HMMT_2',year=year,round=round,authority='ORGANIZER_ARCHIVE'))
 for year in range(1989,2024):out.append(dict(key=f'apmo-{year}',url=f'https://www2.smc.math.ca/Competitions/APMO/exam/apmo{year}.pdf',family='apmo',year=year,authority='MATHEMATICAL_SOCIETY_ARCHIVE'))
 for year in range(2000,2024):out.append(dict(key=f'imosl-{year}',url=f'https://www.imo-official.org/assets/documents/problems/{year}/IMO{year}SL.pdf',family='imo_shortlist',year=year,authority='ORGANIZER_ARCHIVE'))
 for year in range(1985,2024):out.append(dict(key=f'putnam-{year}',url=f'https://mathweb.ucsd.edu/~pfitz/downloads/putnam/putnam{year}.pdf',family='putnam',year=year,authority='UNIVERSITY_PROBLEM_ARCHIVE'))
 return out

def fetch(j):
 d=OUT/'private/sources';p=d/(j['key']+'.pdf');meta=d/(j['key']+'.receipt.json')
 if meta.exists():return json.loads(meta.read_text())
 result=dict(j,retrieved_at=time.time(),status='FAILED')
 try:
  # curl retains TLS validation, supports institutional certificate chain handling.
  r=subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','18',j['url'],'-o',str(p)],capture_output=True)
  if r.returncode:raise ValueError(r.stderr.decode()[:240])
  b=p.read_bytes()
  if not b.startswith(b'%PDF'):raise ValueError('not PDF')
  import fitz
  doc=fitz.open(p);pages=[x.get_text() for x in doc];save(d/(j['key']+'.pages.json'),pages)
  result.update(status='FETCHED',sha256=sha(b),pages=len(pages),path=str(p.relative_to(ROOT)))
 except Exception as e:result['error']=str(e)[:300]
 save(meta,result);return result

def words(s):
 s=unicodedata.normalize('NFKD',s).lower().replace('ﬁ','fi').replace('ﬀ','ff')
 s=re.sub(r'\\[a-z]+',' ',s);return re.findall(r'[a-z]{2,}',s)
def grams(s,n=4):
 w=words(s);return set(' '.join(w[i:i+n]) for i in range(len(w)-n+1))
def match():
 metas=[json.loads(x) for x in (DATA/'host/task_metadata.jsonl').read_text().splitlines()];tasks=[json.loads(x) for x in (DATA/'public/tasks.jsonl').read_text().splitlines()]
 pages=[]
 for p in sorted((OUT/'private/sources').glob('*.pages.json')):
  rec=json.loads(p.with_name(p.name.replace('.pages.json','.receipt.json')).read_text())
  for i,text in enumerate(json.loads(p.read_text())):pages.append((rec,i,text,grams(text)))
 results=[]
 for m,t in zip(metas,tasks):
  gs=grams(t['problem']);rank=[]
  for rec,i,text,gg in pages:
   if gs:
    score=len(gs&gg)/len(gs)
    if score>=.25:rank.append(dict(archive=rec['key'],url=rec['url'],pdf_sha256=rec['sha256'],page=i+1,shared_ngrams=len(gs&gg),ngram_coverage=score,declared_family=rec['family']))
  rank=sorted(rank,key=lambda x:(-x['ngram_coverage'],-x['shared_ngrams'],x['archive'],x['page']))[:5]
  results.append(dict(task_id=t['task_id'],sequence=m['sequence'],source_family=m['source'],candidates=rank,status='CANDIDATE_REQUIRES_ITEM_AND_SEMANTIC_REVIEW' if rank else 'UNKNOWN_ARCHIVE_NO_MATCH'))
 save(OUT/'source_candidates.json',results)
 print('archive candidates',sum(bool(r['candidates']) for r in results),'of',len(results),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='fetch':
  jj=jobs();save(OUT/'retrieval_plan.json',dict(criterion='fixed archives through2023; all200 same phrase retrieval; no model output selection',jobs=jj,paid_model_calls=0))
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
   rr=list(ex.map(fetch,jj))
  save(OUT/'retrieval_summary.json',dict(requested=len(rr),fetched=sum(r['status']=='FETCHED' for r in rr),failed=sum(r['status']!='FETCHED' for r in rr)))
 match()
