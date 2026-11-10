"""Mock model and actual TextWorld / Docker acceptance for recovery acquisition."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from alfworld_.recovery_acquisition import (
    MECHANISM_FIELDS, parse_mechanisms, parse_step_analyses, rank_mechanisms, recovery_view,
)
from alfworld_.skill_acquisition import load_source, recovery_outcome
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read
from failure_evo.run_health import RunUnhealthy
from run_alfworld_skill_acquisition import prepare_recovery, recovery_acceptance, recovery_execution
from test_alfworld_skill_acquisition import SOURCE, response

# Synthetic test artifacts. The production adapter receives neither fixture.
LOCAL = """def environment_operator(c):
    for action in c['admissible_commands']:
        if action.startswith('open '+c['goal'].split()[-1].rstrip('.')+' '):
            return {'status':'applied','action':action,'state':{},'reason':'MOCK fixture'}
    return {'status':'declined','state':{},'reason':'MOCK fixture'}
"""
EXTENDED = """def environment_operator(c):
    count = c['state'].get('count', 0)
    if count < 5 and 'look' in c['admissible_commands']:
        return {'status':'applied','action':'look','state':{'count':count+1},'reason':'MOCK fixture'}
    return {'status':'declined','state':{},'reason':'MOCK fixture'}
"""
DECLINE = """def environment_operator(c):
    return {'status':'declined','state':{},'reason':'MOCK fixture'}
"""


def fixture_sender(wire):
    payload = json.loads(wire['messages'][-1]['content'])
    assert not {'probe','candidate_pool','game_sha256','expert_plan'} & payload.keys()
    if 'events' in payload:
        items = []
        for e in payload['events']:
            anchor = e['anchor']
            items.append(dict(evidence_id=e['evidence_id'], decision='HYPOTHESIS' if e['won'] else 'ABSTAIN',
                failure_evidence_id=e['failure_step_id'],
                recovery_evidence_ids=[e['steps'][anchor][0]],
                cause='MOCK',repair='MOCK',uncertainty='MOCK'))
        # Leave a trace unassigned by abstaining; the first source is retained.
        items[-1]['decision']='ABSTAIN'
        items[-2]['recovery_evidence_ids']=[payload['events'][-2]['steps'][0][0]]
        return response(dict(analyses=items))
    if 'mechanism' in payload:
        mechanism = payload['mechanism']
        code = LOCAL if len(mechanism['evidence_ids']) > 1 else (
            EXTENDED if mechanism['cause']=='MOCK EXTENDED' else DECLINE)
        return response(dict(code=code,description='MOCK',applicability='MOCK'))
    ids = [a['evidence_id'] for a in payload['analyses']]
    return response(dict(mechanisms=[dict({k:'MOCK' for k in MECHANISM_FIELDS}, evidence_ids=group,
                    cause='MOCK EXTENDED' if i==2 else 'MOCK')
                    for i,group in enumerate((ids[:2],ids[2:3],ids[3:4]))],uncertainty='MOCK'))


class OutcomeTest(unittest.TestCase):
    def test_outcomes(self):
        def state(obs, cmds, *, score=0, won=False, action='fixture'):
            return dict(observation=obs,commands=cmds,score=score,won=won,done=won,action=action)
        before = state('before',['alternate'])
        native = state('Nothing happens.',['alternate'])
        prepared = state('prepared',['decisive'])
        won = state('terminal',[],score=1,won=True,action='decisive')
        def assess(alternate, *calls):
            return recovery_outcome(before,native,[prepared,won],alternate,[dict(status=c) for c in calls])
        self.assertEqual(assess([], 'declined')['status'],'DECLINED')
        self.assertEqual(assess([native], 'applied')['status'],'REPAIR_FAILED')
        self.assertEqual(assess([state('other',['irrelevant'])], 'applied')['status'],'PROGRESS_UNVERIFIED')
        self.assertEqual(assess([], 'error')['status'],'POLICY_ERROR')
        self.assertEqual(assess([prepared], 'applied','declined')['status'],'LOCAL_REPAIR_VERIFIED')
        self.assertTrue(assess([prepared,won], 'applied','applied')['episode_won'])


@unittest.skipUnless(SOURCE.exists(),'locked source required')
class RecoveryTest(unittest.TestCase):
    def test_actual_recovery_pipeline_and_resume(self):
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root = Path(os.environ.get('ALFWORLD_RECOVERY_ACCEPTANCE',temp))
            calls=[]
            def sender(wire):
                calls.append(wire)
                return fixture_sender(wire)
            result = recovery_acceptance(SOURCE,root,sender)
            self.assertEqual((result['localized'],result['abstentions'],result['mechanisms']),(14,2,3))
            self.assertEqual([c['support_count'] for c in result['candidates']],[2,1,1])
            self.assertEqual(len(calls),6)
            self.assertEqual(result['rejected_evidence'],2)
            self.assertEqual(result['grounded_hypotheses'],12)
            rejected = read(root/'analyses.json')['rejected']
            self.assertEqual([r['reason'] for r in rejected],['RECOVERY_REFERENCE_NOT_AFTER_FAILURE']*2)
            merge_prompt = calls[2]['messages'][0]['content']
            self.assertIn('same precondition, repair order',merge_prompt)
            self.assertIn('Keep separate or leave unassigned',merge_prompt)
            self.assertTrue(all('Never choose the first available action' in wire['messages'][0]['content']
                                for wire in calls[3:]))
            merge = json.loads(calls[2]['messages'][-1]['content'])['analyses']
            self.assertTrue({r['evidence_id'] for r in rejected}.isdisjoint(a['evidence_id'] for a in merge))
            checks = [v for c in result['candidates'] for v in c['checks']]
            self.assertEqual(checks[0]['status'],'LOCAL_REPAIR_VERIFIED')
            self.assertFalse(checks[0]['episode_won'])
            self.assertEqual(checks[-2]['status'],'DECLINED')
            self.assertEqual(checks[-1]['status'],'PROGRESS_UNVERIFIED')
            self.assertEqual(checks[-1]['alternate_action_count'],5)
            self.assertEqual(checks[-1]['short_window'],4)
            for check in checks:
                self.assertLessEqual(check['alternate_action_count'], min(12,51-check['checkpoint']['step']))
            for wire in calls:
                self.assertNotIn('expert_plan',str(wire))
                self.assertNotIn('candidate_pool',str(wire))
                self.assertNotIn('probe',str(wire))
            for candidate in result['candidates']:
                self.assertEqual(candidate['status'],'SHADOW')
            ledger = (root/'budget.jsonl').read_bytes()
            self.assertEqual(result,recovery_acceptance(SOURCE,root,sender))
            self.assertEqual(ledger,(root/'budget.jsonl').read_bytes())
            self.assertEqual(len(calls),6)
            launch = Path(temp)/'real-prepared'
            prepare_recovery(SOURCE,launch,root)
            grant = read(launch/'authorization.template.json')
            with self.assertRaises(PermissionError):
                recovery_execution(SOURCE,launch,authorization=grant)
            self.assertFalse((launch/'provider.jsonl').exists())
            self.assertTrue(all(e['kind']=='SHADOW_REGISTERED' for e in EvidenceStore(root/'registry.jsonl').records()))

    def test_unknown_stops_b_resume(self):
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root = Path(temp)
            sends = []
            def broken(wire):
                sends.append(wire)
                raise TimeoutError('mock transport interruption')
            with self.assertRaises(TimeoutError):
                recovery_acceptance(SOURCE,root,broken)
            ledger = (root/'budget.jsonl').read_bytes()
            with self.assertRaises(RunUnhealthy):
                recovery_acceptance(SOURCE,root,broken)
            self.assertEqual(len(sends),1)
            self.assertEqual(ledger,(root/'budget.jsonl').read_bytes())
            self.assertEqual(read(root/'interrupted.json')['budget']['calls'],1)

    def test_grounding_abstention_and_ranking(self):
        _,arms,_ = load_source(SOURCE)
        batch = arms['B'][:8]
        parsed = json.loads(fixture_sender({'messages':[dict(content=json.dumps(dict(events=[recovery_view(e,[]) for e in batch])))]})
                            ['choices'][0]['message']['content'])
        analyses = parse_step_analyses(parsed,batch)['analyses']
        eligible = [a['evidence_id'] for a in analyses if a['decision']=='HYPOTHESIS']
        proposals = dict(mechanisms=[dict({k:'test' for k in MECHANISM_FIELDS}, evidence_ids=[i])
                                     for i in reversed(eligible)], uncertainty='test')
        self.assertEqual(rank_mechanisms(parse_mechanisms(proposals,analyses),analyses)[0]['proposal']['evidence_ids'],
                         [eligible[0]])
        proposals['mechanisms'][0]['evidence_ids']=[analyses[-1]['evidence_id']]
        self.assertEqual(parse_mechanisms(proposals,analyses)['rejected'][0]['index'],0)
        first, second, third = parsed['analyses'][:3]
        first['recovery_evidence_ids'] = second['recovery_evidence_ids']
        third['failure_evidence_id'] = 'HOST DIAGNOSTIC CANARY'
        parsed['analyses'].append(dict(second))
        result = parse_step_analyses(parsed,batch)
        reasons = {r['evidence_id']:r['reason'] for r in result['rejected']}
        self.assertEqual(reasons[first['evidence_id']],'RECOVERY_REFERENCE_UNKNOWN_OR_FOREIGN')
        self.assertEqual(reasons[second['evidence_id']],'DUPLICATE_ANALYSIS')
        self.assertEqual(reasons[third['evidence_id']],'FAILURE_REFERENCE_NOT_ANCHOR')
        intact = result['analyses'][0]
        e = next(e for e in batch if e['evidence_id']==intact['evidence_id'])
        self.assertEqual(intact['recovery'][0]['quote'],e['steps'][e['anchor']][1])

    def test_insufficient_evidence_stops_merge(self):
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root = Path(temp)
            calls = []
            def sender(wire):
                calls.append(wire)
                raw = fixture_sender(wire)
                analyses = json.loads(raw['choices'][0]['message']['content'])['analyses']
                return response(dict(analyses=analyses[:1] if len(calls)==1 else []))
            result = recovery_acceptance(SOURCE,root,sender)
            self.assertEqual(result['status'],'INSUFFICIENT_GROUNDED_EVIDENCE')
            self.assertEqual((result['localized'],result['rejected_evidence']),(1,15))
            self.assertEqual(len(calls),2)
            self.assertFalse((root/'merge').exists())


if __name__=='__main__':
    unittest.main()
