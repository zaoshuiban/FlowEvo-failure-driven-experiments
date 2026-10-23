import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from failure_evo.repair_choice import *
from failure_evo.repair_choice_memory import *
from failure_evo.runtime import Budget
from failure_evo.workflow_protocol_v2 import Limits

RULE={'when':{'candidate_state':'STRUCTURAL_PASS','public_result':'WRONG_ANSWER','remaining_calls_min':1},'action':'REGENERATE_FRESH','fallback':'NATIVE'}
TASK=PublicTaskView('task','Print the answer')
FEEDBACK=PublicFeedback.project({'visibility':'public','status':'WRONG_ANSWER','cases':[{'visibility':'public','legal_verified':True,'input':'1','expected':'2','actual':'SOURCE_SENTINEL'}]})
PASS=PublicFeedback.project({'visibility':'public','status':'PUBLIC_PASS','cases':[{'visibility':'public','legal_verified':True,'input':'1','expected':'2','actual':'2'}]})
class Transport:
    def __init__(self):self.sent=[]
    def send(self,prepared,*,task_budget,**kw):
        key=task_budget.reserve(prepared.input_upper,prepared.output_upper)
        self.sent.append(prepared);task_budget.settle(key,10)
        return {'text':'```python\nprint(2)\n```','finish_reason':'stop'}

class Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(parse_rule(canonical(RULE)),RULE)
        for change in ({'action':'STOP'},{'fallback':'STOP'},{'instruction':'hack'}):
            with self.assertRaises(ValueError):validate_rule(dict(RULE,**change))
        with self.assertRaises(ValueError):parse_rule('{"action":1,"action":2}')
        with self.assertRaises(ValueError):validate_rule(dict(RULE,when=dict(RULE['when'],remaining_calls_min=True)))
    def test_projection_and_requests(self):
        a=canonical(action_messages('REPAIR_EXISTING',TASK,'# SOURCE_SENTINEL\nprint(1)',FEEDBACK))
        b=canonical(action_messages('REGENERATE_FRESH',TASK,'# SOURCE_SENTINEL\nprint(1)',FEEDBACK))
        self.assertIn('SOURCE_SENTINEL',a);self.assertNotIn('SOURCE_SENTINEL',b)
        self.assertIn('expected',b)
        with self.assertRaises(TypeError):action_messages('REGENERATE_FRESH',TASK.to_dict(),'',FEEDBACK)
    def test_same_host_and_budget(self):
        transport=Transport();client=RepairChoiceClient(transport,'test');budget=Budget(max_calls=1)
        action=generic_choice('print(1)',FEEDBACK,budget)
        self.assertEqual(action,'REPAIR_EXISTING')
        result=client.attempt(action,TASK,'print(1)',FEEDBACK,budget,lambda *args:PASS)
        self.assertEqual(result['status'],'applied');self.assertEqual(budget.calls,1)
        self.assertEqual(choose(RULE,'print(1)',FEEDBACK,budget),'NATIVE')
        with self.assertRaises(Exception):client.attempt('REGENERATE_FRESH',TASK,'print(1)',FEEDBACK,budget,lambda *args:PASS)
        self.assertEqual(len(transport.sent),1)
    def test_failed_action_retains_original(self):
        c=RepairChoiceClient(Transport(),'test');r=c.attempt('REGENERATE_FRESH',TASK,'print(1)',FEEDBACK,Budget(),lambda *a:FEEDBACK)
        self.assertEqual(r['code'],'print(1)');self.assertEqual(r['fallback'],'NATIVE')
    def test_evidence_levels(self):
        self.assertEqual(assess({'a':False,'b':False},{'a':True,'b':False})['level'],'LOCAL_IMPROVEMENT')
        self.assertEqual(assess({'a':False,'b':True},{'a':True,'b':False})['regressed'],['b'])
        p={'generic':{'a':False},'operator':{'a':False},'generic_cost':2,'operator_full_cost':1}
        self.assertFalse(assess({'a':False},{'a':False},paired=p)['paired_efficiency'])
        p.update(generic={'a':True},operator={'a':True})
        self.assertTrue(assess({'a':True},{'a':True},paired=p)['paired_efficiency'])
        p['operator_full_cost']=None
        with self.assertRaises(ValueError):assess({'a':True},{'a':True},paired=p)
    def test_bounded_generation(self):
        class LearningTransport:
            def __init__(self):self.calls=0
            def send(self,prepared,**kw):
                self.calls+=1
                return {'text':'{"action":"STOP"}' if self.calls==1 else canonical(RULE),'finish_reason':'stop'}
        t=LearningTransport()
        r=generate_rule(t,{'public_failure':'WA'},request_prefix='new-run',limits=Limits(),allow_revision=True)
        self.assertEqual(t.calls,2);self.assertEqual(r['rule'],RULE)
        self.assertIn('diagnosis',r['versions'][0])
    def test_final_preflight_before_send(self):
        t=Transport();c=RepairChoiceClient(t,'small',limits=Limits(input_token_upper=1));b=Budget()
        with self.assertRaises(Exception):c.execute_action('REGENERATE_FRESH',TASK,'print(1)',FEEDBACK,b)
        self.assertEqual(b.calls,0);self.assertEqual(t.sent,[])

    def test_real_entry_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            m=RuleMemory(pathlib.Path(d)/'memory.jsonl');key=m.add(RULE,['evidence:source'])
            c=RepairChoiceClient(Transport(),'test');b=Budget()
            self.assertEqual(run_trial(m,key,c,TASK,'print(1)',FEEDBACK,b,lambda *a:PASS)['status'],'declined')
            self.assertEqual(b.calls,0)
            report=pathlib.Path(d)/'host.json';report.write_text('{}')
            checks=dict.fromkeys(['contract','boundary','negative_cases','fallback','no_known_harm'],True)
            m.record_assessment(key,{'a':False,'b':False},{'a':True,'b':False},report_path=report)
            with self.assertRaises(ValueError):m.authorize(key,tasks=['task'],opportunities=1,safety_checks=checks,authorization_id='auth')
            m.record_assessment(key,{'a':False},{'a':True},report_path=report)
            m.authorize(key,tasks=['task'],opportunities=1,safety_checks=checks,authorization_id='auth')
            self.assertEqual(run_trial(m,key,c,TASK,'print(1)',FEEDBACK,b,lambda *a:PASS)['status'],'applied')
            self.assertEqual(m.state(key)['remaining'],0)
            self.assertEqual(run_trial(m,key,c,TASK,'print(1)',FEEDBACK,b,lambda *a:PASS)['status'],'declined')
            m.archive(key,'no further evidence')
            self.assertEqual(m.state(key)['evidence_refs'],['evidence:source'])
            with self.assertRaises(ValueError):m.propose_relearning(key,['evidence:source'],'try again')
            m.propose_relearning(key,['evidence:new'],'new public evidence changes applicability')
            self.assertEqual(m.state(key)['permission'],'shadow')
            self.assertEqual(RuleMemory(m.path).state(key),m.state(key))

if __name__=='__main__':unittest.main()
