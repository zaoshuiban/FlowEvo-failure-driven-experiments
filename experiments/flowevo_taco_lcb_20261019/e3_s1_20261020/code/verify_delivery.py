"""Read-only, offline artifact/source verification; writes only its audit result."""
import pathlib,json,hashlib,sys,time
R=pathlib.Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={};errors=[]
for name,expected in load(R/'artifact_hashes.json').items():
 p=R/name
 if not p.is_file() or sha(p)!=expected:errors.append(name)
checks['artifact_hashes']=not errors
m=load(R/'review_manifest.json');checks['frozen_48_tasks_224_programs']=len(m['tasks'])==48 and sum(len(x['historical_programs']) for x in m['tasks'])==224
checks['copied_original_programs']=all(sha(R/'review_cards'/t['task_id']/(a['stage']+'.py'))==a['code_sha256'] for t in m['tasks'] for a in t['historical_programs'])
checks['task_sources']=all(sha(R/'source/tasks'/k)==v for k,v in load(R/'source/task_hashes.json').items())
checks['first_replay_pins']=all(sha(R/k)==v for k,v in load(R/'replay_frozen.json')['hashes'].items())
f=load(R/'stress_frozen_v2.json');checks['stress_v2_pins']=sha(R/'stress_suite_v2.json')==f['suite_sha256'] and sha(R/'code/stress_checks_v2.py')==f['code_sha256']
implementation=R/'implementation/FlowEvo'
checks['implementation_matches_local_delivery']=all(sha(implementation/pathlib.Path(k).relative_to('FlowEvo'))==v for k,v in load(R/'implementation_manifest.json').items())
sys.path.insert(0,str(implementation/'src'));from failure_evo.evidence import MechanismStore
store=MechanismStore(R/'mechanism_evidence.jsonl');records=store.events.records();checks['evidence_chain']=len(records)==1
checks['evidence_files']=all(sha(R/f['path'])==f['sha256'] for row in records for f in row['payload']['files'].values())
checks['no_active_operators']=load(R/'mechanisms_verified.json')['active_operators']==0
checks['scoring_acceptance']=load(R/'scoring_validation.json')['status']=='PASS'
vendor=R.parent.parent.parent/'vendor/FlowEvo'
if pathlib.Path('/opt/flowevo-benchmark-20261019').exists():
 base=pathlib.Path('/opt/flowevo-benchmark-20261019');candidates=list(base.glob('**/src/compiler/gatekeeper.py'));before=load(R/'source/vendor_before.json');matches=[]
 for p in candidates:
  v=p.parents[2]
  if v==implementation:continue
  if all((v/k).is_file() and sha(v/k)==h for k,h in before['python_file_hashes'].items()):matches.append(str(v))
 checks['original_vendor_64_files_unchanged']=bool(matches)
 result_extra={'original_vendor_matches':matches}
else:result_extra={}
out={'status':'PASS' if all(checks.values()) else 'FAIL','checked_at_unix':time.time(),'checks':checks,'hash_mismatches':errors,**result_extra}
(R/'delivery_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
