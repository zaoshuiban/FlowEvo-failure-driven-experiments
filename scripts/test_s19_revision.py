"""New compile envelope and diversity schedule, entirely zero API."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from test_s19_v2 import H,rule,tasks,plan,Provider,FakeJudge
from run_learning_stream import LearningStream
from failure_evo.learning_contract import normalize,VERSION
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.compile_queue import CompileQueue

class Tests(unittest.TestCase):
 def test_strict_normalization(self):
  base=dict(hypothesis=H,rule=rule())
  for metadata in ({},{'type':'json_object'}):
   a=normalize(json.dumps(dict(base,**metadata)));self.assertTrue(a['accepted']);self.assertEqual(a['normalized'],base)
  invalid=[]
  for key,val in [('type','object'),('type',{}),('permission','experimental'),('budget',10),('unknown',0)]:invalid.append(dict(base,**{key:val}))
  for where,key in [('hypothesis','permission'),('rule','permission'),('when','type')]:
   x=copy.deepcopy(base);target=x['rule']['when'] if where=='when' else x[where];target[key]='x';invalid.append(x)
  for val in ('',None,{},[]):
   x=copy.deepcopy(base);x['hypothesis']['action']=val;invalid.append(x)
  for x in invalid:
   with self.subTest(x=x):self.assertFalse(normalize(json.dumps(x))['accepted'])
  self.assertFalse(normalize(json.dumps(base),'length')['accepted'])
  self.assertFalse(normalize('{"type":"json_object","type":"json_object"}')['accepted'])
  self.assertIn('permission',normalize(json.dumps(dict(base,permission='active')))['error'])
 def test_new_entry_and_rule_dedup(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();p=plan();p.update(compile_protocol=VERSION,scheduler_protocol='evidence-diversity-v1');p['protocol_hash']=e.fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
   def factory(ch):
    send=provider.factory(ch)
    def wrapped(wire):
     out=send(wire)
     if ch=='learning':
      m=out['choices'][0]['message'];m['content']=json.dumps(dict(json.loads(m['content']),type='json_object'))
     return out
    return wrapped
   runner=e.ExperimentRunner(Path(tmp)/'F',p,factory);stream=LearningStream(runner,tasks(),batch_size=1);stream.run()
   audits=[e.read(f) for f in (runner.folder/'jobs').glob('*/*-normalization.json')]
   self.assertTrue(audits);self.assertTrue(all(a['accepted'] for a in audits))
   with stream.memory._transaction() as (rows,_):
    self.assertEqual(sum(x['event']=='CANDIDATE_SAVED' for x in rows),2)
    self.assertTrue(any(x['event']=='EQUIVALENT_GENERATION_RECORDED' for x in rows))
    self.assertTrue(any(x.get('decision')=='SUSPEND' for x in rows))
   self.assertTrue(list((runner.folder/'jobs').glob('*/*-capability.json')))
 def test_scheduler_diversity_and_prefix(self):
  from failure_evo.evidence import EvidenceStore
  with tempfile.TemporaryDirectory() as tmp:
   facts=[dict(event_id=str(i),task_id=t,provenance_group_id=t) for i,t in enumerate(['a','a','b','c'])]
   class Store:
    def visible(self,at,stream):return facts[:3] if at<10 else facts
   index=SymptomLearning(Path(tmp)/'h',Store(),'run',scheduler_protocol='evidence-diversity-v1')
   for key,ids,finish,artifact in [('one',['0'],'length','STRUCTURAL_PASS'),('two',['1'],'stop','STRUCTURAL_PASS'),('cross',['2','3'],'length','NO_COMPLETE_CODE')]:
    state=dict(hypothesis_id=key,version=1,source_evidence_ids=ids,supporting_evidence_ids=[],contradicting_evidence_ids=[],effects=[],linked_operator_versions=[],applicable_actions=['REGENERATE_FRESH'],symptom=dict(artifact=artifact,finish_reason=finish,actions=['REGENERATE_FRESH']))
    index.events.append('HYPOTHESIS_VERSION',state,0)
   jobs=index.schedule(at=10,budget_available=True)
   self.assertEqual(len(jobs),2);self.assertEqual(jobs[0]['hypothesis_id'],'cross')
   self.assertEqual(len(jobs[1]['evidence_ids']),2)
   self.assertTrue(all(j['priority_basis']['no_common_root_cause_claim'] for j in jobs))
   for j in jobs:index.start(j,11);index.finish(j,None,11)
   self.assertEqual(index.schedule(at=13,budget_available=True),[])
   self.assertEqual(index.schedule(at=14,budget_available=False),[])
 def test_source_diversity_budget_and_unknown_state(self):
  from failure_evo.evidence import EvidenceStore
  with tempfile.TemporaryDirectory() as tmp:
   facts=[dict(event_id='a',task_id='same',provenance_group_id='lineage'),dict(event_id='b',task_id='same',provenance_group_id='lineage')]
   class Store:
    def visible(self,at,stream):return facts
   index=SymptomLearning(Path(tmp)/'h',Store(),'run',scheduler_protocol='evidence-diversity-v1')
   for key,artifact in [('a','STRUCTURAL_PASS'),('b','NO_ENTRY')]:
    state=dict(hypothesis_id=key,version=1,source_evidence_ids=[key],supporting_evidence_ids=[],contradicting_evidence_ids=[],effects=[],linked_operator_versions=[],applicable_actions=['REGENERATE_FRESH'],symptom=dict(artifact=artifact,finish_reason='stop',actions=['REGENERATE_FRESH']))
    index.events.append('HYPOTHESIS_VERSION',state,0)
   jobs=index.schedule(at=1,budget_available=True);self.assertEqual(len(jobs),1)
   decisions=[r['payload'] for r in index.events.records() if r['kind']=='SCHEDULE_DECISION']
   self.assertEqual(sum(d['reason']=='SOURCE_DIVERSITY_LIMIT' for d in decisions),1)
   index.start(jobs[0],2)
   self.assertEqual(index.schedule(at=3,budget_available=True),[])
   self.assertEqual(index.schedule(at=4,budget_available=False),[])
 def test_formal_rule_does_not_authorize_partial(self):
  from failure_evo.repair_choice_memory import RuleMemory,assess
  with tempfile.TemporaryDirectory() as tmp:
   m=RuleMemory(Path(tmp)/'r','repair-choice-json-v2');key=m.add(rule(),['a'])
   report=Path(tmp)/'assessment.json';report.write_text('{}')
   a=m.record_assessment(key,{'a':False,'b':False},{'a':True,'b':False},report_path=report)
   self.assertEqual(a['level'],'LOCAL_IMPROVEMENT')
   with self.assertRaises(ValueError):m.authorize(key,tasks=['future'],opportunities=1,safety_checks={k:True for k in ('contract','boundary','negative_cases','fallback','no_known_harm')},authorization_id='test')
   self.assertEqual(m.state(key)['permission'],'shadow')
   self.assertFalse(assess({'a':False},{'a':False},paired=dict(generic={'a':False},operator={'a':False},generic_cost=2,operator_full_cost=1))['paired_efficiency'])
if __name__=='__main__':unittest.main()
