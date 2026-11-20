"""Engineering fixtures only; no new-game collection or model calls."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import run_alfworld_route_b5_transfer as X


class B5Tests(unittest.TestCase):
    def test_candidates_exact_and_joint_changes(self):
        paths={'S11':X.PARENT/'S11_3/initial/candidate.py','FR11':X.PARENT/'FR11_0/behavior/candidate.py',
               'Route_A':X.A3/'frozen_candidate/gate.py','S0':X.B.CODE}
        for k,p in paths.items():self.assertEqual(X.A.sha(p),X.EXPECTED[k])
        self.assertNotEqual(X.A.digest(X.EXPECTED),X.A.digest(dict(X.EXPECTED,S0='changed')))
        src=paths['Route_A'].read_text();adapt=X.B.worker_artifact(src)
        self.assertTrue(adapt.startswith(src));self.assertTrue(X.P.static_check_detailed(adapt)['passed'])

    def test_reservation_only_is_not_training_exposure(self):
        t=dict(game_sha256='a',trajectory_sha256='b',group='c')
        a=dict(protected_games=[dict(task=t,reasons=['ALLOCATED_OR_RESERVED:'+str(X.RESERVATION)])])
        self.assertEqual(X.exposure_decision(t,a),[])
        a['protected_games'][0]['reasons'].append('LOG_REFERENCE:executed.jsonl')
        self.assertEqual(X.exposure_decision(t,a),['LOG_REFERENCE:executed.jsonl'])

    def test_group_and_trajectory_overlap_excluded(self):
        t=dict(game_sha256='a',trajectory_sha256='b',group='c')
        for k in ('group','trajectory_sha256'):
            old=dict(game_sha256='x',trajectory_sha256='y',group='z');old[k]=t[k]
            self.assertTrue(X.exposure_decision(t,dict(protected_games=[dict(task=old,reasons=['used'])])))

    def test_choose_three_preserves_equal_length_pair(self):
        rows=[dict(mode='READY',label=l,physical_state_group_id='p',public_history_scope=dict(complete=False)) for l in ('MATCH','UNKNOWN')]
        rows+=[dict(mode='TARGET_CONFLICT',label='DECLINE',physical_state_group_id='n'),dict(mode='OTHER_INSTANCE',label='MATCH',physical_state_group_id='o')]
        self.assertEqual(X.choose_samples(rows),rows[:3])

    def test_simple_tasks_do_not_fabricate_unknown(self):
        rows=[dict(mode='READY',label='MATCH',physical_state_group_id='p')]
        self.assertEqual(X.choose_samples(rows),rows)

    def test_collection_pending_blocks_without_reexecution(self):
        e=[dict(kind='GAME_STARTED',payload=dict(id='a'))]
        with self.assertRaises(X.P.RunUnhealthy):X.C.check_pending(e)

    def test_environment_pending_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'env.jsonl';events=X.P.EvidenceStore(p)
            events.append('STEP_STARTED',dict(index=1,scope='prefix',branch='a'),time.time())
            with self.assertRaises(X.P.RunUnhealthy):X.P.EnvironmentReceipts(p,50)

    def test_budget_and_hash_change_block(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=dict(run_id='fixture',max_calls=0,max_tokens=0,max_cost_microusd=0,worker_calls=0)
            budget=X.B.create_accounts(root,p)
            with self.assertRaises(X.B.BudgetExhausted):budget.reserve(1,1)
            with self.assertRaises(X.B.BudgetExhausted):budget.tool()
            f=root/'source';f.write_text('a');old=X.A.sha(f);f.write_text('b')
            with self.assertRaises(PermissionError):X.P.verify_history({str(f):old})

    def fixture(self,label='MATCH'):
        p=X.A.read(X.PARENT/'protocol.json');c=next(c for c in p['validation'] if c['label']==label)
        o=c['origin'];prefix=o['steps'][:o['projected']['anchor']];ids=c['ids']
        return dict(label=label),o,prefix if ids is None else [prefix[i-1] for i in ids]

    def test_no_action_is_not_intervention_or_completion(self):
        s,o,v=self.fixture();score=X.score(s,o,v,None)
        self.assertEqual(score['actions'],0);self.assertFalse(score['completed_repair']);self.assertTrue(score['declined'])

    def test_open_only_is_not_completed_repair(self):
        s,o,v=self.fixture();failed=o['steps'][o['projected']['anchor']-1]['action'];target=failed.rsplit(' to ',1)[-1]
        a=dict(action='open '+target,observation='You open the '+target+'.',commands=[failed],won=False)
        r=X.score(s,o,v,dict(actions=[a],stop='DECLINED'))
        self.assertTrue(r['barrier_removed']);self.assertFalse(r['delivery_confirmed']);self.assertFalse(r['completed_repair'])

    def test_unknown_observation_not_automatically_false(self):
        s,o,v=self.fixture('UNKNOWN');a=dict(action='look',observation='Visible state',commands=[],won=False)
        r=X.score(s,o,v,dict(actions=[a],stop='DECLINED'))
        self.assertFalse(r['unsupported_recovery']);self.assertTrue(r['safety_unresolved'])

    def test_temporal_evidence_used_only_after_observed(self):
        s,o,v=self.fixture('UNKNOWN');failed=o['steps'][o['projected']['anchor']-1]['action'];target=failed.rsplit(' to ',1)[-1]
        a=dict(action='open '+target,observation='You open the '+target+'.',commands=[failed],won=False)
        with patch.object(X,'processed',side_effect=lambda history,*_:any(x['action']=='look' for x in history)):
            # Synthetic truth function tests chronological access, not mathematics.
            v=[x for x in v if x['action']!='look']
            before=X.score(s,o,v,dict(actions=[a],stop='DECLINED'))
            after=X.score(s,o,v,dict(actions=[dict(a,action='look'),a],stop='DECLINED'))
        self.assertTrue(before['unsupported_recovery']);self.assertFalse(after['unsupported_recovery'])

    def test_unknown_no_retroactive_entry_credit(self):
        s,o,v=self.fixture('UNKNOWN');failed=o['steps'][o['projected']['anchor']-1]['action']
        a=dict(action='open '+failed.rsplit(' to ',1)[-1],observation='opened',commands=[failed],won=False)
        with patch.object(X,'processed',return_value=False):r=X.score(s,o,v,dict(actions=[a],stop='DECLINED'))
        self.assertTrue(r['temporal'][0]['unsupported'])

    def test_missing_decisive_suffix_is_not_exception(self):
        s,o,v=self.fixture('DECLINE');prefix=o['steps'][:o['projected']['anchor']]
        r=X.P.score_source(dict(o,steps=prefix),prefix,[],[],'DECLINED')
        self.assertEqual(r['outcome'],'DECLINED')


if __name__=='__main__':unittest.main()
