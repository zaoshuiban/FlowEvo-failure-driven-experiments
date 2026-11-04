import sys,re,json
from pathlib import Path
sys.path.insert(0,'scripts')
from audit_math_stream200_sources import *
segments=[]
for f in sorted((OUT/'private/sources').glob('*.pages.json')):
 rec=json.loads(f.with_name(f.name.replace('.pages.json','.receipt.json')).read_text())
 if rec['key'].startswith('gate-'):continue
 pages=json.loads(f.read_text());offset=0;offsets=[]
 for p in pages:offsets.append(offset);offset+=len(p)+1
 full='\n'.join(pages)
 fam=rec['family'];rx=r'(?m)^([ACGN]\d{1,2})\.?\s' if fam=='imo_shortlist' else r'(?m)^([AB][1-6])\.?\s' if fam=='putnam' else r'(?m)^(?:(?:Question|Problem)\s+)?(\d{1,2})[.:]\s' if fam.startswith('HMMT') else r'(?m)^(?:Question|Problem)\s+(\d{1,2})\.?\s' if fam=='apmo' else r'(?m)^(?:Problem\s+|\d{4}/)(\d)[.:]\s'
 mm=list(re.finditer(rx,full));seen=set()
 for k,m in enumerate(mm):
  item=m[1]
  if item in seen:continue
  seen.add(item)
  text=full[m.end():mm[k+1].start() if k+1<len(mm) else len(full)]
  # prevent a source solution block from being used as task text; preservation stays in private PDF.
  text=re.split(r'(?im)^\s*(?:solution|answer|shortlisted problems . solutions)\b',text)[0]
  page=max(i for i,o in enumerate(offsets) if o<=m.start())+1
  segments.append(dict(archive=rec['key'],url=rec['url'],authority=rec['authority'],pdf_sha256=rec['sha256'],family=fam,year=rec['year'],item=item,page=page,text=text.strip()))
metas=[json.loads(x) for x in (DATA/'host/task_metadata.jsonl').read_text().splitlines()];tasks=[json.loads(x) for x in (DATA/'public/tasks.jsonl').read_text().splitlines()]
rank=[]
for m,t in zip(metas,tasks):
 gs=grams(t['problem']);rr=[]
 for seg in segments:
  sg=grams(seg['text']);shared=gs&sg;score=len(shared)/max(1,len(gs));precision=len(shared)/max(1,len(sg))
  if score>=.4 and precision>=.25:rr.append(dict(**seg,coverage=score,precision=precision))
 rr=sorted(rr,key=lambda s:(-(s['coverage']+s['precision'])/2,s['archive']))[:2]
 rank.append(dict(task_id=t['task_id'],sequence=m['sequence'],dataset_source=m['source'],problem=t['problem'],candidates=rr))
save(OUT/'private/archive_segments.json',segments);save(OUT/'private/item_review_candidates.json',rank)
print('segments',len(segments),'candidate200',sum(bool(r['candidates']) for r in rank))
