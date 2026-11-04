"""Reception-v2 continuation; import exact proposal, not fresh mechanism generation."""
import json,time,sys
from pathlib import Path
import run_v42_delivery_repair as r
from failure_evo.delivery_reception import receive,VERSION
FIRST=r.OUT;NEW=r.ROOT/'runs/flowevo_v42_delivery_20261029_02'
r.OUT=NEW;r.Adapter.protocol='v42-delivery-repair-v2'
def freeze():
 if (NEW/'freeze.json').exists():raise RuntimeError('already frozen')
 NEW.mkdir(parents=True,exist_ok=True)
 for rel in ['parent.py','parent_manifest.json','public_source.json','private/development.json','private/new_confirmation.json']:
  dst=NEW/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((FIRST/rel).read_bytes())
 raw=r.load(FIRST/'jobs/C-properties-1/reception.json')['raw_value'];receipt=receive('properties',raw)
 assert receipt['status']=='ACCEPTED' and receipt['protected_content_unchanged']
 assert r.fingerprint(raw)==r.fingerprint(receipt['normalized'])
 r.save(NEW/'proposal_import.json',dict(origin='HISTORICAL_REAL_MODEL_RESPONSE_FROM_CURRENT_DELIVERY_STUDY',source=str(FIRST/'jobs/C-properties-1/provider.jsonl'),source_sha256=r.sha(FIRST/'jobs/C-properties-1/provider.jsonl'),raw=raw,receipt=receipt,new_induction_calls=0))
 original=r.load(FIRST/'candidate_freeze.json')['versions']['B-R'];r.save(NEW/'ordinary_revision_import.json',dict(origin='UNCHANGED_REAL_ORDINARY_REVISION',source=str(FIRST/'candidate_freeze.json'),artifact=original,source_sha256=r.sha(FIRST/'candidate_freeze.json')))
 r.save(NEW/'ordinary_feedback.json',r.load(FIRST/'ordinary_feedback.json'))
 p=r.load(FIRST/'protocol.json');p.update(version=r.Adapter.protocol,at=time.time(),normalization_version=VERSION,continuation_of=FIRST.name,induction_imported=True,new_confirmation_exposure='Same30 frozen before first attempt; FIRST never executed/evaluated confirmation. Still withheld from all model requests.',reception_bound=dict(properties=32,test_specs=64),execution_selection='first eight test specs in original property order, at most16 input executions; all unexecuted proposals retained as NOT_EVALUATED_BUDGET, not dropped',additional_model_calls='C revision plus at most one delivery clarification and one compliance repair; no re-generation, ordinary arm imported unchanged')
 files=[Path(__file__),Path(r.__file__),r.ROOT/'scripts/v42_oracles.py',r.ROOT/'scripts/v4_test_data.py',r.ROOT/'scripts/run_v42_properties.py']+list((r.ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 p['source_hashes']={str(f.relative_to(r.ROOT)):r.sha(f) for f in files};p['data_hashes']={str(f.relative_to(NEW)):r.sha(f) for f in [NEW/'parent.py',NEW/'parent_manifest.json',NEW/'public_source.json',NEW/'private/development.json',NEW/'private/new_confirmation.json',NEW/'proposal_import.json',NEW/'ordinary_revision_import.json']}
 r.save(NEW/'protocol.json',p);r.save(NEW/'freeze.json',dict(hash=r.fingerprint(p)))
 for rel in p['source_hashes']:
  dst=NEW/'frozen_source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((r.ROOT/rel).read_bytes())
 r.save(NEW/'history_hashes.json',{str(f.relative_to(r.ROOT)):r.sha(f) for root in [r.OLD,r.V4,FIRST,r.ROOT/'runs/hard140_algorithm_20261028_01'] for f in root.rglob('*') if f.is_file()})
 print('FROZEN',r.fingerprint(p))
def run():
 r.verify()
 if (NEW/'STARTED.json').exists():raise RuntimeError('consumed run')
 r.save(NEW/'STARTED.json',dict(at=time.time()));parent=r.load(NEW/'parent_manifest.json');a=dict(status='STATIC_VALID',sha256=parent['sha256'],path=str(NEW/'parent.py'));versions={'parent':a,'B-R':r.load(NEW/'ordinary_revision_import.json')['artifact']}
 try:
  proposal=r.load(NEW/'proposal_import.json')['receipt']['normalized']
  # No trimming needed for this received proposal; assertions protect the frozen execution budget.
  assert sum(len(p['tests']) for p in proposal['properties'])<=8
  receipt=r.assess(a,proposal);r.save(NEW/'properties.json',dict(proposal=proposal,receipt=receipt))
  counter=any(x['verdict']['status']=='ALGORITHM_COUNTEREXAMPLE' for x in receipt['records']);r.save(NEW/'C_gate.json',dict(counterexample_established=counter,source_sha256=a['sha256']))
  if not counter:versions['C']=dict(status='NOT_REVISED',reason='no trusted algorithm counterexample')
  else:
   base=dict(r.load(NEW/'public_source.json'),previous_code=(NEW/'parent.py').read_text())
   value=r.deliver('C','revision',dict(base,analysis=proposal,diagnostics=receipt));child=r.make_artifact('C',value,a['sha256'])
   if child['status']=='STATIC_REJECTED':
    fixed=r.deliver('C','compliance',dict(r.load(NEW/'public_source.json'),previous_code=value['code'],diagnostics=child['review']));child=r.make_artifact('C-compliance',fixed,child['sha256'])
   versions['C']=child
  r.save(NEW/'candidate_freeze.json',dict(at=time.time(),versions=versions));r.save(NEW/'GENERATION_COMPLETE.json',dict(at=time.time()));print('GENERATED',versions['C']['status'])
 except BaseException as e:r.save(NEW/'STOP.json',dict(at=time.time(),reason=str(e)));raise
if __name__=='__main__':
 if sys.argv[1]=='evaluate':r.evaluate()
 else:globals()[sys.argv[1]]()
