"""Offline Git-object audit; findings never print credential values or answers."""
import argparse,subprocess,json,hashlib,re,collections
from pathlib import Path
from check_public_commit import SECRET_PATTERNS
KEYWORDS=re.compile(r'private|gold|gate|oracle|token|key',re.I)

def audit(commit,repo):
 names=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=repo,text=True).splitlines()
 rows=[];reviews=[];credentials=[];model_origins=collections.Counter();response_ids=collections.Counter()
 for path in names:
  data=subprocess.check_output(['git','show',commit+':'+path],cwd=repo)
  findings=[rule for rule,p in SECRET_PATTERNS if p.search(data)]
  if findings:credentials.append(dict(path=path,rules=findings))
  if path.startswith(('FlowEvo/src/','scripts/')):category='SOURCE_OR_TEST'
  elif path.endswith('.md'):category='PUBLIC_REPORT'
  elif path.startswith('reports/post_pilot50_end_to_end/'):category='ENGINEERING_ARTIFACT_OR_AUDIT_METADATA'
  else:category='REQUIRES_REVIEW'
  rows.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),category=category,keyword_path=bool(KEYWORDS.search(path)),credential_rules=findings))
  if path.endswith('reviewed_cases.private.json'):
   obj=json.loads(data);originals=[r.get('original_id','') for role in ('Development','Gate') for r in obj[role]]
   reviews.append(dict(path=path,origin=obj.get('origin'),all_mock_originals=all(x.startswith('MOCK_') for x in originals),cases=len(originals)))
  if path.endswith('.jsonl'):
   for line in data.splitlines():
    try:r=json.loads(line)
    except ValueError:continue
    payload=r.get('payload',{})
    if r.get('kind')=='MATH_SHADOW':model_origins[payload.get('origin','MISSING')]+=1
    if r.get('kind')=='RAW_RESPONSE':
     raw=payload.get('response',{});id=str(raw.get('id',''))
     response_ids['ENGINEERING_PREFIX' if id.startswith(('engineering-','mock')) else 'OTHER_OR_MISSING']+=1
 return dict(commit=commit,files=rows,counts=dict(collections.Counter(r['category'] for r in rows)),keyword_files=sum(r['keyword_path'] for r in rows),credential_findings=credentials,review_packages=reviews,shadow_origins=dict(model_origins),raw_response_id_classes=dict(response_ids),scope='Only changed files in this commit; not all Git history; no hidden value printed')
def main():
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
 result=audit(a.commit,repo);path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');path.chmod(0o600)
 print(json.dumps({k:v for k,v in result.items() if k not in ('files','review_packages')},ensure_ascii=False))
if __name__=='__main__':main()
