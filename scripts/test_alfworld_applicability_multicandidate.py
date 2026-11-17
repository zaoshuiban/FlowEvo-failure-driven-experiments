"""A2 engineering fixtures. No fixture is a model-discovered strategy."""
from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from alfworld_ import recovery_applicability_learning as L
from alfworld_.recovery_acquisition import RecoveryAdapter,stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from failure_evo.contracts import canonical,fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_skill_acquisition import create_accounts
import run_alfworld_applicability_multicandidate as study
from test_alfworld_skill_acquisition import response
from test_alfworld_python_recovery_feedback import receipt_hashes

ROOT=Path(os.environ.get('ALFWORLD_A2_OUTPUT',study.ROOT/'runs/alfworld_route_a_a2_20261113_01'))


def gate(status,comment=''):
    return f"def applicability_gate(context):\n    return {{'status':{status!r},'reason':'MOCK ENGINEERING ONLY'}}\n"+comment


def propose(code):return dict(decision='PROPOSE',code=code,description='ENGINEERING FIXTURE',applicability='Not learned')


def fixture_roles():
    roles=L.load_dataset(study.DATA)
    # Independent ENGINEERING row, not an additional A1b observation or label.
    unknown=deepcopy(roles['TRAIN'][0]);unknown.update(sample_id='ENGINEERING_unknown',role='TRAIN_VALIDATION',
        game_sha256='ENGINEERING_GAME',physical_state_group_id='ENGINEERING_STATE',label='UNKNOWN',
        candidate_context=dict(goal='ENGINEERING ONLY',observation='Unresolved public evidence.',
                               admissible_commands=['look'],history=[dict(action='look',observation='Unresolved public evidence.')]),
        label_evidence=[dict(kind='ENGINEERING_FIXTURE_NOT_ENVIRONMENT_FACT')],reason='ENGINEERING uncertainty')
    unknown.pop('source_key');roles['TRAIN_VALIDATION'].append(unknown)
    return roles


def fixtures():
    return {'candidate_0/v0':response(propose(gate('UNKNOWN'))),
            'candidate_1/v0':response(propose(gate('MATCH'))),
            'candidate_2/v0':response(propose('import os\n'+gate('DECLINE'))),
            'candidate_3/v0':response({'decision':'PROPOSE','code':gate('DECLINE')}),
            'candidate_0/v1':response(propose(gate('MATCH','# revised candidate zero\n'))),
            'candidate_1/v1':response(propose(gate('UNKNOWN'))),
            'candidate_2/v1':response(propose(gate('MATCH','# revised candidate two\n'))),
            'candidate_3/v1':response(dict(decision='ABSTAIN',reason='MOCK cannot repair'))}


def sender_for(responses,wires):
    def sender(wire):
        wires.append(wire);p=json.loads(wire['messages'][1]['content'])
        return responses[p['candidate_id']+('/v1' if 'parent_version' in p else '/v0')]
    return sender


def fresh(name):
    ROOT.mkdir(mode=0o700,exist_ok=True);output=ROOT/name
    if output.exists():raise FileExistsError('Keep earlier test run; choose a new acceptance directory')
    return output


class CoreTests(unittest.TestCase):
    def test_real_data_coverage_and_strict_projection(self):
        roles=L.load_dataset(study.DATA)
        self.assertFalse(L.coverage(roles)['ready'])
        packet=L.training_packet(roles['TRAIN'],study.CODE.read_text())
        raw=canonical(packet)
        for key in ('recovery_probe','game_sha256','source_key','check_rule','label_evidence'):
            self.assertNotIn('"'+key+'":',raw)
        with self.assertRaises(PermissionError):L.training_packet(roles['TRAIN_VALIDATION'],study.CODE.read_text())

    def test_same_length_different_labels_are_not_inferred_by_host(self):
        rows=deepcopy(L.load_dataset(study.DATA)['TRAIN'][:2])
        rows[0]['label']='MATCH';rows[1]['label']='DECLINE'
        for row in rows:row['candidate_context']['history']=[{'action':'look','observation':'fixture'}]
        m=L.metrics([dict(expected=r['label'],actual='MATCH') for r in rows])
        self.assertEqual((m['match_coverage'],m['false_applicability']),(1,1))

    def test_errors_are_distinct(self):
        for expected,actual,error in [('MATCH','DECLINE','FALSE_REJECTION'),('DECLINE','MATCH','FALSE_APPLICABILITY'),
             ('UNKNOWN','MATCH','UNSUPPORTED_MATCH'),('MATCH','ERROR','WORKER_ERROR')]:
            self.assertEqual(L.classify(expected,actual),error)

    def test_no_role_or_physical_state_leakage(self):
        roles=fixture_roles();roles['TRAIN_VALIDATION'][0]['physical_state_group_id']=roles['TRAIN'][0]['physical_state_group_id']
        with self.assertRaises(PermissionError):L.validate_rows(roles)

    def test_no_foreign_feedback_or_validation(self):
        roles=L.load_dataset(study.DATA);row=roles['TRAIN'][0]
        a=dict(candidate_id='a',version='v',code='previous',delivery={},revision=0,status='STATIC_PASSED',
            train=[dict(candidate_id='other',version='v',role='TRAIN',sample_id=fingerprint(row['sample_id']))])
        with self.assertRaises(PermissionError):L.feedback(a,roles['TRAIN'],{})
        a['train'][0].update(candidate_id='a',role='TRAIN_VALIDATION')
        with self.assertRaises(PermissionError):L.feedback(a,roles['TRAIN'],{})

    def test_revision_limits_abstention_duplicates(self):
        for status in ('ABSTAIN','DUPLICATE_SOURCE','INPUT_LIMIT'):
            self.assertFalse(L.needs_revision(dict(status=status,revision=0)))
        self.assertFalse(L.needs_revision(dict(status='STATIC_REJECTED',revision=1)))
        self.assertTrue(L.needs_revision(dict(status='SCHEMA_REJECTED',revision=0)))

    def test_all_decline_no_eligible_and_coverage_are_different(self):
        roles=fixture_roles()
        a=dict(candidate_id='c0',revision=0,version='v',code_sha256='c',status='STATIC_PASSED',
               train=[dict(expected=r['label'],actual='DECLINE') for r in roles['TRAIN']],
               validation=[dict(expected=r['label'],actual='DECLINE') for r in roles['TRAIN_VALIDATION']])
        self.assertEqual(L.select([a],roles,engineering=True)['status'],'NO_ELIGIBLE_CANDIDATE')
        self.assertEqual(L.select([a],L.load_dataset(study.DATA))['status'],'DATA_COVERAGE_BLOCKED')

    def test_fixed_selection_and_best_initial(self):
        roles=fixture_roles()
        def candidate(cid,bad):
            return dict(candidate_id=cid,revision=0,version=cid,code_sha256=cid,status='STATIC_PASSED',
                train=[dict(expected=r['label'],actual='MATCH' if bad else r['label']) for r in roles['TRAIN']],
                validation=[dict(expected=r['label'],actual='MATCH' if bad else r['label']) for r in roles['TRAIN_VALIDATION']])
        candidates=[candidate('c0',True),candidate('c1',False)]
        chosen=L.select(candidates,roles,engineering=True)
        self.assertEqual(chosen['selected']['candidate_id'],'c1')
        self.assertEqual(chosen['engineering_status'],'ENGINEERING_SELECTION_VALID')
        self.assertEqual(L.select(list(reversed(candidates)),roles,engineering=True),chosen)

    def test_temperature_default_wire_and_request_binding(self):
        with TemporaryDirectory() as d:
            root=Path(d);packet={}
            a=study.wire(root,packet,'test',0);b=study.wire(root,packet,'test',0.6)
            self.assertEqual(a['temperature'],0);self.assertEqual(b['temperature'],0.6)
            self.assertNotEqual(fingerprint(a),fingerprint(b))
            with self.assertRaises(ValueError):study.wire(root,packet,'test',float('nan'))

    def test_old_s1_default_wire_is_byte_equivalent(self):
        path=study.ROOT/'runs/alfworld_container_boundary_learning_20261113_02/provider.jsonl'
        old=next(r['payload']['wire'] for r in EvidenceStore(path).records() if r['kind']=='SEND_STARTED')
        payload=json.loads(old['messages'][1]['content'])
        with TemporaryDirectory() as tmp:
            provider=RecoveryAdapter(Path(tmp)/'provider.jsonl',None,model=old['model'],mock=True,sender=lambda _:None,
                stage='analyze',payload=payload,parser=parse_delivery,analysis_prompt=old['messages'][0]['content'],max_wire_input_upper=65536)
            actual=provider.preflight(dict(phase='induction',max_tokens=old['max_tokens'],
                discovery=dict(stage='analyze',payload_sha256=fingerprint(payload))))
            self.assertEqual(canonical(actual),canonical(old))

    def test_mock_requests_unknown_and_budget(self):
        with TemporaryDirectory() as d:
            root=Path(d);plan=dict(run_id='mock:unknown',max_calls=8,max_tokens=557056,max_cost_microusd=700000,worker_calls=1)
            budget=create_accounts(root,plan);calls=[]
            def sender(wire):calls.append(wire);raise TimeoutError('MOCK unknown')
            with self.assertRaises(Exception):stage_request(root,'candidate_0/v0','analyze',{},parse_delivery,budget,sender=sender,temperature=0.6)
            with self.assertRaises(RunUnhealthy):stage_request(root,'candidate_0/v0','analyze',{},parse_delivery,budget,sender=sender,temperature=0.6)
            self.assertEqual(len(calls),1)
            self.assertTrue(budget.snapshot()['unknown_or_pending_requests'])
            self.assertTrue(any(r['kind']=='SEND_UNKNOWN' for r in EvidenceStore(root/'provider.jsonl').records()))
        with TemporaryDirectory() as d:
            root=Path(d);budget=create_accounts(root,dict(plan,max_calls=0));calls=[]
            with self.assertRaises(BudgetExhausted):stage_request(root,'job','analyze',{},parse_delivery,budget,sender=lambda wire:calls.append(wire))
            self.assertEqual(calls,[])


class ArchivedReceiptsTests(unittest.TestCase):
    """Read the final retained acceptance, without new Worker/environment steps."""
    def setUp(self):
        self.root=study.ROOT/'runs/alfworld_route_a_a2_20261113_01/final_acceptance/actual_a1b'
        if not (self.root/'result.json').exists():self.skipTest('retained acceptance not available')

    def test_each_revised_source_starts_with_complete_original_prefix(self):
        result=read(self.root/'result.json');steps=EvidenceStore(self.root/'environment.jsonl').records()
        branches={}
        for attempt in result['attempts']:
            for row in attempt.get('train',[])+attempt.get('validation',[]):
                live=row['live']
                if not live.get('won'):continue
                branch=live['evaluation_branch']
                branches.setdefault(row['sample_id'],set()).add(branch)
                prefix=[r for r in steps if r['kind']=='STEP_STARTED' and r['payload']['branch']==branch
                        and r['payload']['scope']=='prefix']
                self.assertGreater(len(prefix),0)
                self.assertFalse(any(r['kind']=='STEP_STARTED' and r['payload']['branch']==branch
                                 and r['payload']['scope'].startswith('resume') for r in steps))
        self.assertEqual(len(branches),4)
        self.assertTrue(all(len(ids)==3 for ids in branches.values()))

    def test_four_initial_requests_precede_revisions_and_validation_ids_are_absent(self):
        roles=read(self.root/'roles.private.json')
        forbidden={fingerprint(r['sample_id']) for r in roles['TRAIN_VALIDATION']}
        sends=[r['payload'] for r in EvidenceStore(self.root/'provider.jsonl').records() if r['kind']=='SEND_STARTED']
        packets=[json.loads(r['wire']['messages'][1]['content']) for r in sends]
        self.assertEqual(len({r['key'] for r in sends}),8)
        self.assertEqual({p['candidate_id'] for p in packets[:4]},{f'candidate_{i}' for i in range(4)})
        self.assertTrue(all('parent_version' not in p for p in packets[:4]))
        self.assertTrue(all('parent_version' in p for p in packets[4:]))
        for packet in packets:
            raw=canonical(packet)
            self.assertFalse(any(key in raw for key in forbidden))
            self.assertNotIn('check_rule',raw)


@unittest.skipUnless(os.environ.get('ALFWORLD_A2_REAL_ACCEPTANCE')=='1','explicit real Worker/TextWorld zero-API acceptance')
class RealExecutionTests(unittest.TestCase):
    def test_01_four_candidates_training_revision_and_blocked_data(self):
        output=fresh('actual_a1b');study.prepare(output)
        wires=[];result=study.run(output,sender=sender_for(fixtures(),wires))
        self.assertEqual(len(wires),8)
        self.assertEqual(result['selection']['status'],'DATA_COVERAGE_BLOCKED')
        self.assertIsNone(result['regression']);self.assertFalse((output/'selected.json').exists())
        attempts=result['attempts'];self.assertEqual(len({a['payload_sha256'] for a in attempts[:4]}),4)
        self.assertTrue(all(w['temperature']==0.6 for w in wires))
        self.assertIn('SCHEMA_REJECTED',{a['status'] for a in attempts})
        self.assertIn('STATIC_REJECTED',{a['status'] for a in attempts})
        self.assertIn('DUPLICATE_SOURCE',{a['status'] for a in attempts})
        for a in attempts:
            if a['revision']:
                parent=next(p for p in attempts if p['version']==a['parent_version'])
                request=read(output/a['candidate_id']/'v1/request.private.json')['payload']
                self.assertEqual(request['previous_code'],parent['code'])
                self.assertEqual(a['parent_source_sha256'],parent['code_sha256'])
                self.assertEqual({r['sample_id'] for r in request['own_train_feedback']},
                                 {r['sample_id'] for r in parent.get('train',[])})
                self.assertNotIn('validation',request)
        rows=[r for a in attempts for r in a.get('train',[])]
        self.assertTrue(any(r['live'].get('won') for r in rows))
        self.assertTrue(all(r['live'].get('evaluation_branch') for r in rows if r['live'].get('won')))
        for a in attempts:
            if 'registration' in a:
                self.assertEqual(a['registration']['status'],'SHADOW')
        before=receipt_hashes(output)
        self.assertEqual(study.run(output,sender=lambda _:self.fail('duplicate request')),result)
        self.assertEqual(receipt_hashes(output),before)
        with self.assertRaisesRegex(PermissionError,'DATA_COVERAGE_BLOCKED'):study.run(output)
        self.assertEqual(sha(study.CODE),L.RECOVERY_SHA)

    def test_02_engineering_selection_freeze_and_exposed_regression(self):
        output=fresh('engineering_selection');study.prepare(output,fixture_roles=fixture_roles())
        # Same four independent requests; no training repair for abstentions.
        values={f'candidate_{i}/v0':response(dict(decision='ABSTAIN',reason='MOCK')) for i in range(4)}
        values['candidate_0/v0']=response(propose(gate('MATCH')))
        values['candidate_0/v1']=response(propose(gate('MATCH')))
        wires=[];result=study.run(output,sender=sender_for(values,wires))
        self.assertEqual(result['selection']['engineering_status'],'ENGINEERING_SELECTION_VALID')
        self.assertEqual(result['selection']['status'],'SELECTED_PENDING_REGRESSION')
        self.assertIsNone(result['selection']['research_winner'])
        self.assertTrue(result['regression']['retention_passed'])
        self.assertEqual(sum(r['role']=='EXPOSED_SOURCE' for r in result['regression']['rows']),11)
        self.assertEqual(sum(r['role']=='EXPOSED_BOUNDARY' for r in result['regression']['rows']),21)
        self.assertTrue((output/'selected.json').exists())
        self.assertEqual(result['paid_requests'],0)

    def test_03_interrupted_then_settled_response_reentry(self):
        output=fresh('resume');study.prepare(output);wires=[]
        values={f'candidate_{i}/v0':response(dict(decision='ABSTAIN',reason='MOCK')) for i in range(4)}
        def crash(a):raise RuntimeError('ENGINEERING interruption after persisted attempt')
        with self.assertRaisesRegex(RuntimeError,'interruption'):
            study.run(output,sender=sender_for(values,wires),after_attempt=crash)
        self.assertEqual(len(wires),1)
        result=study.run(output,sender=sender_for(values,wires))
        self.assertEqual((len(wires),result['budget']['calls']),(4,4))
        self.assertEqual(result['budget']['unknown_or_pending_requests'],[])

    def test_04_real_worker_decline_unknown_exceptions_and_bad_envelope(self):
        output=fresh('worker_errors');study.prepare(output);wires=[]
        codes=[gate('DECLINE'),gate('UNKNOWN'),
               'def applicability_gate(context):\n    raise ValueError("MOCK")\n',
               'def applicability_gate(context):\n    return {"status":"MATCH"}\n']
        values={f'candidate_{i}/v0':response(propose(code)) for i,code in enumerate(codes)}
        values.update({f'candidate_{i}/v1':response(dict(decision='ABSTAIN',reason='MOCK')) for i in range(4)})
        result=study.run(output,sender=sender_for(values,wires))
        initial=result['attempts'][:4]
        self.assertEqual([{r['actual'] for r in a['train']} for a in initial],
                         [{'DECLINE'},{'UNKNOWN'},{'ERROR'},{'ERROR'}])
        self.assertFalse(result['environment'])


if __name__=='__main__':unittest.main()
