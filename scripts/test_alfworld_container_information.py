"""B3 injected-model engineering acceptance; fixtures are not learned results."""
import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
import run_alfworld_container_information as E
from alfworld_.route_b_compact_projection import decode
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
P=E.P;M=E.M
PRE=E.ROOT/'runs/alfworld_route_b3_container_preparation_20261116_03'
DECLINE="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'ENGINEERING_ONLY'}\n"

def response(content,n=1):
    return dict(id='MOCK-'+str(n),model='deepseek-flash',usage=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120),
        choices=[dict(message=dict(content=P.canonical(content)),finish_reason='stop')])

def proposal(code):return dict(decision='PROPOSE',code=code,description='ENGINEERING_ONLY',applicability='ENGINEERING_ONLY')

def empty_eval(row,p,budget,out):
    sources=[]
    for c in p['cases']:
        sources.append(dict(source_ref=c['id'],stop='DECLINED',won=False,actions=[],decisions=[dict(
            operator=dict(status='declined',state={},reason='own:'+row['version']),worker_status='OK',
            selected_action=None,receipt=None,candidate_error=None)]))
    return dict(candidate_version=row['version'],code_sha256=row['code_sha256'],sources=sources,
        controls=[],metrics=dict(repairs=0,deliveries=0,won=0,errors=0,incompatible=0,unsupported=0,actions=0,controls_declined=2))

class ProjectionTests(unittest.TestCase):
    def setUp(self):self.p=P.read(PRE/'protocol.json')
    def test_same_fragments_and_raw_steps_no_synthetic_history(self):
        packs=M.packets(self.p['cases'])
        for i,c in enumerate(self.p['cases']):
            s,f,fr=(packs[a]['examples'][i] for a in M.ARMS)
            self.assertEqual(s['R'],fr['R']);self.assertEqual(f['F'],fr['F']);self.assertNotIn('R',f);self.assertNotIn('F',s)
            self.assertEqual(s['C'],f['C']);self.assertNotIn('Nothing happens.',s['C']['observation'])
            self.assertFalse(s['R']['start_context']['observation_included'])
            o=c['origin'];a=o['projected']['anchor'];self.assertEqual(s['R']['first_step'],a+1)
            for block in (f['F'],s['R']):
                for r in block['steps']:
                    orig=o['steps'][int(r['step_id'].split('_')[1])-1]
                    for key in ('action','observation','done','won'):self.assertEqual(r[key],orig[key])
        self.assertEqual(len(packs['S']['examples'][-1]['R']['steps']),8)
        for a in M.ARMS:
            body=E.wire(PRE,packs[a],'initial')
            self.assertEqual(body['messages'][0]['content'],M.PROMPTS['initial']);self.assertEqual(body['temperature'],.6)
            self.assertEqual(decode(json.loads(body['messages'][1]['content'])),packs[a])

    def test_feedback_own_only_no_original_R_or_labels(self):
        row=dict(version='v',code_sha256='s');ev=empty_eval(row,self.p,None,None)
        ev['private_witness']='PRIVATE_CANARY';ev['other_candidate']='OTHER_CANARY'
        pack=M.behavior_payload(DECLINE,'v',self.p['cases'],ev,lambda _:True)
        self.assertNotIn('PRIVATE_CANARY',P.canonical(pack));self.assertNotIn('OTHER_CANARY',P.canonical(pack))
        self.assertNotIn('strict_witness',P.canonical(pack));self.assertNotIn('recovery_probe',P.canonical(pack))
        self.assertEqual(pack['previous_code'],DECLINE)
        with self.assertRaises(PermissionError):M.behavior_payload(DECLINE,'foreign',self.p['cases'],ev,lambda _:True)
        limited=M.behavior_payload(DECLINE,'v',self.p['cases'],ev,lambda x:sum(len(y['decisions']) for y in decode(x)['own_execution_feedback'])<=3)
        self.assertEqual([len(x['decisions']) for x in limited['own_execution_feedback']],[1,1,1]+[0]*8)
        with self.assertRaises(ValueError):M.behavior_payload(DECLINE,'v',self.p['cases'],ev,lambda _:False)

    def test_selection_denominators_and_no_all_decline_promotion(self):
        self.assertEqual(M.choose([])['status'],'NO_ELIGIBLE_CANDIDATE')
        x=dict(id='F_0',version='v',model_tokens=120,evaluation=empty_eval(dict(version='v',code_sha256='s'),self.p,None,None))
        self.assertIsNone(M.choose([x])['selected'])
        x['evaluation']['metrics']['repairs']=1;y=deepcopy(x);y['id']='F_1'
        self.assertEqual(M.choose([y,x])['selected'],'F_0')
        x['evaluation']['metrics']['errors']=1;self.assertEqual(M.choose([x,y])['selected'],'F_1')
        parent=dict(candidate_version='p',code_sha256='s',metrics=dict(repairs=1,errors=0,incompatible=0,unsupported=0,actions=2))
        lineage=dict(id='S_0',arm='S',model_tokens=240,initial_evaluation=parent,evaluation=None,attempts=[dict(id='S_0/initial',version='p')])
        self.assertEqual(M.choose(M.evaluated_versions([lineage]))['selected'],'S_0/initial')

class SchedulerTests(unittest.TestCase):
    def test_paired_bridge_preserves_real_history_and_remaining_budget(self):
        from prepare_alfworld_container_confirmation import paired_bridge
        from types import SimpleNamespace as NS
        from alfworld_.generator import AlfWorldStepOutput
        history=['prior']*48;snapshot={'L2':['frozen']};seen=[]
        native=NS(step=lambda **kw:(seen.append(deepcopy(kw)) or AlfWorldStepOutput(action='look',model_calls=1)))
        policy=NS(native=native,states={},used=[],errors=set(),finalize=lambda _:None)
        def step(**kw):
            if not policy.used:policy.used.append('fixture');return AlfWorldStepOutput(action='look',model_calls=0)
            return native.step(**kw)
        policy.step=step
        bridge=paired_bridge(native,policy,{'history':history},snapshot,P.fingerprint(snapshot))
        kw=dict(task_goal='g',observation='Nothing happens.',admissible_commands=['look'],action_history=history,observation_history=['prior']*48,skill_context='L2',policy_directives=['L3'])
        bridge.step(**kw)
        kw.update(observation='actual new observation',action_history=history+['look'],observation_history=['prior']*48+['actual new observation'])
        bridge.step(**kw);self.assertEqual(seen,[kw])
        kw['action_history']=history+['look','look']
        with self.assertRaises(RunUnhealthy):bridge.step(**kw)
        with self.assertRaises(PermissionError):paired_bridge(native,None,{'history':history},snapshot,'wrong')

    def test_36_requests_barriers_own_feedback_and_resume(self):
        sent=[];executed=[]
        def sender(w):
            payload=decode(json.loads(w['messages'][1]['content']));phase=next(k for k,v in M.PROMPTS.items() if v==w['messages'][0]['content'])
            sent.append((phase,payload))
            if phase=='initial':return response(proposal('import os\n'+DECLINE),len(sent))
            if phase=='engineering':
                self.assertEqual(set(payload),{'parent_version','previous_source_or_delivery','engineering_diagnostics'})
                return response(proposal(DECLINE),len(sent))
            self.assertEqual(payload['previous_code'],DECLINE)
            for src in payload['own_execution_feedback']:
                self.assertEqual(src['decisions'][0]['candidate_self_report']['reason'],'own:'+payload['parent_version'])
            return response(proposal(DECLINE+'\n# behavior fixture\n'),len(sent))
        def evaluate(row,p,b,out):
            self.assertTrue((out/'initials_complete.json').exists());self.assertGreaterEqual(len(sent),24)
            executed.append(row['version']);return empty_eval(row,p,b,out)
        with tempfile.TemporaryDirectory(dir=E.ROOT/'runs') as d:
            out=Path(d)/'mock'
            once=[]
            def fault(point,name):
                if not once:once.append(name);raise InterruptedError('after settled response')
            with self.assertRaises(InterruptedError):E.run_mock(PRE,out,sender=sender,evaluate=evaluate,fault=fault)
            self.assertEqual(len(sent),1)
            result=E.run_mock(PRE,out,sender=sender,evaluate=evaluate)
            self.assertEqual(len(sent),36);self.assertEqual(len(executed),24);self.assertEqual(result['paid_requests'],0)
            self.assertEqual([x[0] for x in sent][-12:],['behavior']*12)
            self.assertTrue(all(len(x['attempts'])==3 for x in result['lineages']))
            self.assertTrue(all(v['selected'] is None for v in result['selection'].values()))
            hashes={str(f):P.sha(f) for f in out.rglob('*.jsonl')}
            again=E.run_mock(PRE,out,sender=lambda _:self.fail('request resent'),evaluate=lambda *args:self.fail('evaluation repeated'))
            self.assertEqual(again,result);self.assertEqual(hashes,{str(f):P.sha(f) for f in out.rglob('*.jsonl')})

    def test_abstention_and_behavior_delivery_failure_no_fourth_call(self):
        calls=[]
        def sender(w):
            phase=next(k for k,v in M.PROMPTS.items() if v==w['messages'][0]['content']);calls.append(phase)
            if phase=='behavior':return response(dict(code='invalid'),len(calls))
            return response(proposal(DECLINE) if len(calls)<=4 else dict(decision='ABSTAIN',reason='fixture'),len(calls))
        with tempfile.TemporaryDirectory(dir=E.ROOT/'runs') as d:
            r=E.run_mock(PRE,Path(d)/'mock',sender=sender,evaluate=empty_eval)
            self.assertEqual(len(calls),16);self.assertNotIn('engineering',calls)
            self.assertEqual(sum(x['current']['status']=='ABSTAIN' for x in r['lineages']),8)
            self.assertEqual(sum(x['current']['status']=='DELIVERY_REJECTED' for x in r['lineages']),4)

    def test_unknown_budget_and_no_paid_entry(self):
        with tempfile.TemporaryDirectory(dir=E.ROOT/'runs') as d:
            out=Path(d)/'mock';calls=[]
            def sender(w):calls.append(w);raise TimeoutError('MOCK send unknown')
            with self.assertRaises(TimeoutError):E.run_mock(PRE,out,sender=sender,evaluate=empty_eval)
            with self.assertRaises(RunUnhealthy):E.run_mock(PRE,out,sender=sender,evaluate=empty_eval)
            self.assertEqual(len(calls),1)
            with self.assertRaises(PermissionError):E.run_mock(PRE,out,sender=None,evaluate=empty_eval)
            plan=dict(P.read(PRE/'protocol.json'),max_calls=0)
            budget=E.account(Path(d)/'empty',plan)
            with self.assertRaises(BudgetExhausted):budget.reserve(1,1)

if __name__=='__main__':unittest.main()
