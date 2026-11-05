"""Check staged bytes, not working files. Mechanical boundary, not semantic DLP."""
import argparse,json,re,subprocess,sys
from pathlib import PurePosixPath,Path

PUBLIC_JSON={'source_manifest.json','validation_matrix.json','artifact_integrity_manifest.json','historical_integrity.json','public_audit_summary.json'}
PRIVATE_PARTS={'private','.private','sealed','credentials','generated_artifacts','frozen_source','wire'}
SECRET_PATTERNS=[
 ('PRIVATE_KEY',re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
 ('PROVIDER_KEY',re.compile(rb'\bsk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{24,}')),
 ('BEARER_CREDENTIAL',re.compile(rb'(?i)Bearer\s+[A-Za-z0-9_.-]{24,}')),
 ('ASSIGNED_CREDENTIAL',re.compile(rb'''(?i)["']?(?:OPENAI_API_KEY|DEEPSEEK_API_KEY|ACCESS_TOKEN|SECRET_KEY)["']?\s*[:=]\s*["']([A-Za-z0-9_./+-]{20,})["']''')),
]
PRIVATE_ANSWER=re.compile(rb'''["'](?:gold_answer|reference_answer|official_solution|gate_secret|private_expected)["']\s*:\s*(?!null\b)[^\r\n,}]+''')

def inspect(path,data):
 p=PurePosixPath(path);parts={x.lower() for x in p.parts};name=p.name.lower();errors=[];root=p.parts[0].lower() if p.parts else ''
 if parts & PRIVATE_PARTS or '.private.' in name or name in {'private_publication.jsonl','credentials.json','token.json','tokens.json'}:
  errors.append('PRIVATE_PATH')
 if re.search(r'(?:gold[_-]?answers?|gate[_-]?(?:answers?|keys?|secrets?)|private[_-]?(?:answers?|scores?)|sealed[_-]?answers?)',name) and p.suffix.lower() in {'.json','.yaml','.yml','.toml','.txt'}:errors.append('PRIVATE_DATA_FILE')
 if name.startswith('.env') or p.suffix.lower() in {'.pem','.key','.p12','.pfx'}:errors.append('CREDENTIAL_FILE')
 if root in {'runs','datasets','logs','smoke-results'}:errors.append('LOCAL_ARTIFACT_ROOT')
 if root=='reports':
  if len(p.parts)>3 or not (p.suffix=='.md' or p.name in PUBLIC_JSON):errors.append('RAW_REPORT_ARTIFACT')
  if p.suffix=='.md' and len(data)>512*1024:errors.append('REPORT_TOO_LARGE_REVIEW_REQUIRED')
 if p.suffix in {'.jsonl','.log'}:errors.append('EXECUTION_LOG')
 if p.suffix.lower() in {'.zip','.gz','.tgz','.tar','.7z','.parquet','.sqlite','.db'}:errors.append('BINARY_ARCHIVE_OR_RAW_DATA')
 if name.endswith(('.lock','.tmp')) or '__pycache__' in parts or p.suffix=='.pyc':errors.append('TRANSIENT_FILE')
 for rule,pattern in SECRET_PATTERNS:
  if pattern.search(data):errors.append(rule)
 if p.suffix in {'.json','.jsonl','.md','.yaml','.yml','.toml','.txt'} and PRIVATE_ANSWER.search(data):errors.append('PRIVATE_ANSWER_FIELD')
 if root=='reports' and p.name in PUBLIC_JSON:
  try:value=json.loads(data)
  except (ValueError,UnicodeError):errors.append('INVALID_PUBLIC_MANIFEST')
 return sorted(set(errors))

def staged(repo,commit=None):
 names=subprocess.check_output((['git','diff-tree','--root','--no-commit-id','--name-only','--diff-filter=ACMR','-r','-z',commit] if commit else ['git','diff','--cached','--name-only','--diff-filter=ACMR','-z']),cwd=repo).split(b'\0')
 findings=[]
 for raw in names:
  if not raw:continue
  path=raw.decode('utf-8');data=subprocess.check_output(['git','show',(commit or '')+':'+path],cwd=repo)
  rules=inspect(path,data)
  if rules:findings.append(dict(path=path,rules=rules))
 return findings

def main():
 parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--staged',action='store_true');group.add_argument('--commit');args=parser.parse_args()
 if args.commit and not re.fullmatch(r'(?:[0-9a-fA-F]{7,64}|HEAD(?:~[0-9]+)?)',args.commit):parser.error('use a commit SHA or HEAD')
 repo=subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()
 findings=staged(repo,args.commit)
 print(json.dumps(dict(status='BLOCKED' if findings else 'PASS',findings=findings),ensure_ascii=False,indent=2))
 if findings:
  print('Keep raw/private artifacts outside Git. Publish reviewed summaries and hashes; do not bypass with --no-verify.',file=sys.stderr)
 return bool(findings)
if __name__=='__main__':sys.exit(main())
