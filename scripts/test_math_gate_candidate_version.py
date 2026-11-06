"""Only Operator Contract changes: no old review/release reuse; zero API."""
import copy,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from test_operator_contract import ContractTests
from failure_evo.operator_contract import binding,candidate_identity
from failure_evo.math_gate_pool import AutomatedGateProvider,SealedGateProvider,PoolReviewedRelease,VERSION,review_version
from failure_evo.math_stream_learning import ReviewedRelease
from failure_evo.math_stream import save,sha
from failure_evo.evidence import EvidenceStore
from failure_evo.run_health import RunUnhealthy
from code_math.no_gold import PublicMathTask

class VersionTests(ContractTests):
 def setUp(self):
  super().setUp();self.root=Path(self.tmp.name)
  self.a.update(contract={'parameter_schema':json.dumps({'type':'object'})},excluded_task_ids=['s1','s2'])
  self.a['candidate_version']=binding(self.a)
  self.b=copy.deepcopy(self.a);self.b['operator_contract']['failure_modes'].append('new restriction')
  self.b['candidate_version']=binding(self.b)
  self.assertEqual(self.a['code_sha256'],self.b['code_sha256']);self.assertNotEqual(candidate_identity(self.a),candidate_identity(self.b))
  tasks=[PublicMathTask('s1','public source1'),PublicMathTask('s2','public source2')]
  pool={'origin':'ENGINEERING_FIXTURE','cases':[dict(task_id='g'+str(i),original_id='gate'+str(i),problem='public gate'+str(i),answer='1',oracle_sha256='fixture') for i in range(4)]}
  pp=self.root/'pool.json';save(pp,pool)
  refs=self.root/'scores.jsonl';refs.write_text(''.join(json.dumps(dict(task_id=t.task_id,gold_answer='1'))+'\n' for t in tasks))
  states=EvidenceStore(self.root/'states')
  for i,t in enumerate(tasks):states.append('PRIVATE_SCORED',dict(task_id=t.task_id,sequence=i+1,verdict={'status':'CONFIRMED_WRONG'}),time.time())
  self.paths=[]
  def path(cutoff,key):self.paths.append(key);return self.root/'jobs'/key
  learner=SimpleNamespace(capacity=lambda *a,**k:True,_path=path)
  self.s=SimpleNamespace(path=self.root,engineering=True,tasks=tasks,lineage={'s1':{'source_original_id':'source-original'},'s2':{'source_original_id':'source-original2'}},arms={'F':dict(states=states,learner=learner)},plan=dict(gate_pool_binding=dict(path=str(pp),sha256=sha(pp)),gate_reviewers=['fixture'],cumulative_input_bindings=dict(private_scoring=dict(path=str(refs),sha256=sha(refs)))))
  self.provider=SealedGateProvider(self.s,'F')
 def review(self,a,legacy=False):
  result=dict(version=VERSION if legacy else review_version(a),artifact_sha256=a['code_sha256'],pool_sha256=self.s.plan['gate_pool_binding']['sha256'],reviewer='fixture',review_method='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION',Development=[dict(task_id='s'+str(i+1),supported=i==0,parameters={} if i==0 else None,reason='fixture',assumption_quotes=['public source'+str(i+1)]) for i in range(2)],Gate=[dict(task_id='g'+str(i),supported=i<2,parameters={} if i<2 else None,reason='fixture',assumption_quotes=['public gate'+str(i)]) for i in range(4)])
  if not legacy:result['candidate_version']=candidate_identity(a)
  return result
 def release(self,provider=None):
  r=PoolReviewedRelease.__new__(PoolReviewedRelease);r.stream=self.s;r.arm='F';r.packages=provider or (lambda *a:None);r.journal=EvidenceStore(self.root/'release.jsonl');return r
 def event(self,r,kind,a,**kwargs):
  r.journal.append(kind,dict(candidate_version=candidate_identity(a),sha=a['code_sha256'],**kwargs),time.time())
 def test_review_paths_and_requests_differ(self):
  self.assertNotEqual(self.provider.review_path(self.a),self.provider.review_path(self.b))
  self.assertIsNone(self.provider(self.a,2));self.assertIsNone(self.provider(self.b,2))
  for a in (self.a,self.b):self.assertTrue(self.provider.root.joinpath(candidate_identity(a)+'.request.json').exists())
 def test_changed_frozen_gate_pool_rejected(self):
  pool=Path(self.s.plan['gate_pool_binding']['path'])
  pool.write_text(pool.read_text()+' ')
  with self.assertRaisesRegex(PermissionError,'Gate pool drift'):
   SealedGateProvider(self.s,'F')
 def test_automatic_preflight_rejects_missing_validator_or_profiles(self):
  self.s.plan.update(gate_mode='AUTOMATED_GATE',stop_for_gate_review=False,
                     operator_contract_shadow='pre-score-one-candidate-v1')
  with self.assertRaisesRegex(PermissionError,'trusted automatic Gate validator'):
   AutomatedGateProvider(self.s,'F')
  self.s.plan['automatic_gate_validator']='split-exact-rational-v1'
  with self.assertRaisesRegex(PermissionError,'frozen automated applicability'):
   AutomatedGateProvider(self.s,'F')
 def test_old_code_named_review_not_read(self):
  save(self.provider.root/(self.a['code_sha256']+'.json'),self.review(self.a,legacy=True))
  self.assertIsNone(self.provider(self.a,2))
 def test_copy_review_to_new_path_rejected(self):
  save(self.provider.review_path(self.b),self.review(self.a))
  with self.assertRaises(PermissionError):self.provider(self.b,2)
 def test_freezes_separate_per_contract(self):
  for a in (self.a,self.b):
   save(self.provider.review_path(a),self.review(a));package=self.provider(a,2)
   self.assertEqual(package['candidate_version'],candidate_identity(a))
  freezes=[r['payload']['candidate_version'] for r in self.provider.events.records() if r['kind']=='REVIEW_FROZEN']
  self.assertEqual(freezes,[candidate_identity(self.a),candidate_identity(self.b)])
 def test_completed_A_not_completed_B(self):
  r=self.release();self.event(r,'RELEASE_COMPLETED',self.a,result={'status':'A_ONLY'})
  self.assertEqual(r.attempt(self.a,2,self.root)['status'],'A_ONLY')
  self.assertEqual(r.attempt(self.b,2,self.root)['status'],'SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE')
  self.assertEqual([x['candidate_version'] for x in r.pending_records()],[candidate_identity(self.b)])
 def test_unversioned_completion_not_upgraded(self):
  r=self.release();r.journal.append('RELEASE_COMPLETED',dict(sha=self.a['code_sha256'],result={'status':'OLD'}),time.time())
  self.assertEqual(r.attempt(self.a,2,self.root)['status'],'SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE')
 def test_new_version_job_key_and_recovery(self):
  r=self.release(lambda *a:{'Gate':[{}]});self.event(r,'RELEASE_COMPLETED',self.a,result={'status':'A_ONLY'})
  with patch.object(ReviewedRelease,'attempt',return_value={'status':'B_VALIDATED_SEPARATELY'}) as base:
   self.assertEqual(r.attempt(self.b,2,self.root)['status'],'B_VALIDATED_SEPARATELY')
   r.attempt(self.b,2,self.root);self.assertEqual(base.call_count,1)
  self.assertEqual(self.paths,['gate-'+candidate_identity(self.b)])
 def test_interrupted_identity_scoped(self):
  r=self.release();self.event(r,'RELEASE_STARTED',self.a)
  with self.assertRaises(RunUnhealthy):r.attempt(self.a,2,self.root)
  self.assertEqual(r.attempt(self.b,2,self.root)['status'],'SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE')
 def test_deferred_keeps_artifact_and_polls_once(self):
  r=self.release(lambda *a:{'Gate':[{}]})
  with patch.object(ReviewedRelease,'attempt',return_value={'status':'SHADOW_RELEASE_STAGES_PENDING'}):r.attempt(self.b,2,self.root)
  record=r.pending_records()[0];self.assertEqual(record['artifact'],self.b)
  with patch.object(r,'attempt') as attempt:r.poll(3);attempt.assert_called_once()
 def test_legacy_review_compatibility(self):
  a=copy.deepcopy(self.a);a.pop('operator_contract');a.pop('candidate_version')
  save(self.provider.review_path(a),self.review(a,legacy=True))
  self.assertIsNotNone(self.provider(a,2))
 def test_gate_freeze_and_shard_consumption_version_scoped(self):
  from failure_evo.operator_version_gate import VersionGate
  reg=VersionGate(self.root/'gate-registry')
  for a in (self.a,self.b):
   reg.freeze_gate([a],data_hash='same-pool',development_ids=['d'],gate_ids=['g'])
   reg.record_review(a,[],role='Gate',data_hash='same-pool',exposed=False)
  with self.assertRaises(PermissionError):reg.record_review(self.b,[],role='Gate',data_hash='same-pool',exposed=False)
 def test_completed_A_does_not_hide_B_review_barrier(self):
  from failure_evo.math_cumulative_stream import CumulativeStream
  r=self.release(self.provider)
  self.event(r,'RELEASE_COMPLETED',self.a,result={'status':'A_ONLY'})
  self.event(r,'RELEASE_PENDING',self.b,artifact=self.b,path=str(self.root))
  state=SimpleNamespace(plan={'stop_for_gate_review':True},path=self.root,tasks=[1,2,3],arms={x:{'learner':SimpleNamespace(release=r)} for x in ('T','F')})
  self.assertTrue(CumulativeStream._awaiting_reviews(state))
 def test_unversioned_deferred_can_only_use_legacy_pending(self):
  r=self.release();a=copy.deepcopy(self.a);a.pop('operator_contract');a.pop('candidate_version')
  r.journal.append('RELEASE_PENDING',dict(sha=a['code_sha256'],artifact=a,path=str(self.root)),time.time())
  r.journal.append('RELEASE_DEFERRED',dict(sha=a['code_sha256'],path=str(self.root)),time.time())
  self.assertEqual(r.pending_records()[0]['artifact'],a)
 def test_stale_declared_candidate_version_rejected(self):
  a=copy.deepcopy(self.a);a['operator_contract']['algorithm']='changed'
  with self.assertRaises(PermissionError):self.provider.review_path(a)
 def test_base_release_rejects_wrong_package_before_execution(self):
  r=ReviewedRelease(self.s,'F',lambda *a:dict(origin='ENGINEERING_FIXTURE',artifact_sha256=self.a['code_sha256'],candidate_version=candidate_identity(self.a)))
  with self.assertRaises(PermissionError):r.attempt(self.b,2,self.root)
if __name__=='__main__':unittest.main()
