"""Credibility checks for state pairing, budgets and public-prefix selection.

Synthetic fixtures here validate the harness only; never learning evidence.
"""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import run_alfworld_route_c_bounded_learning as C


def row(action, observation, won=False):
    return dict(action=action,observation=observation,commands=['look','inventory'],won=won,done=won,score=float(won))


class Credibility(unittest.TestCase):
    def test_retake_uses_identity_and_destination(self):
        seq=[row('move keychain 2 to shelf 1','You move the keychain 2 to the shelf 1.'),
             row('take keychain 1 from shelf 1','You pick up the keychain 1 from the shelf 1.'),
             row('take keychain 2 from shelf 1','You pick up the keychain 2 from the shelf 1.')]
        self.assertEqual(C.retake_anchors('find two keychain and put them in shelf.',seq),[3])
        self.assertEqual(C.retake_anchors('find two keychain and put them in armchair.',seq),[])

    def test_single_processing_task_is_excluded(self):
        seq=[row('move potato 1 to microwave 1','You move the potato 1 to the microwave 1.'),
             row('take potato 1 from microwave 1','You pick up the potato 1 from the microwave 1.')]
        self.assertEqual(C.retake_anchors('put a hot potato in fridge.',seq),[])

    def test_trigger_prefix_invariance_and_no_outcome_dependency(self):
        seq=[row('move x 1 to shelf 1','You move the x 1 to the shelf 1.'),
             row('take x 1 from shelf 1','You pick up the x 1 from the shelf 1.'),
             row('look','room',True)]
        for n in range(1,4):
            self.assertEqual(C.retake_anchors('put two x in shelf.',seq[:n]),[x for x in C.retake_anchors('put two x in shelf.',seq) if x<=n])
        changed=copy.deepcopy(seq)
        for s in changed:s['won']=not s['won'];s['score']=99
        self.assertEqual(C.retake_anchors('put two x in shelf.',seq),C.retake_anchors('put two x in shelf.',changed))

    def test_public_context_has_no_scores_or_outcomes(self):
        h=C.history([row('look','room',True)])
        self.assertEqual(h,[dict(action='look',observation='room')])
        ctx=C.context_view('goal','room',['look'],h,{})
        self.assertEqual(set(ctx),{'goal','observation','admissible_commands','history','state'})

    def test_native_parser_divergence_is_visible(self):
        p=C.parsed_action('Think: move it\nAct: put x 1 on shelf 1',['look','inventory'])
        self.assertTrue(p['different']);self.assertEqual(p['actual'],'look')

    def harness(self,root,decision):
        obj=C.Study.__new__(C.Study);obj.root=Path(root)
        calls=[];actions=[]
        def model(*a,**k):
            calls.append(a);return dict(text='Act: look',cache=False,usage={})
        def step(action):
            actions.append(action)
            return SimpleNamespace(observation='room',admissible_commands=['look','inventory'],won=False,done=False,score=0)
        env=SimpleNamespace(step=step,close=lambda:None)
        obj.reset=lambda case:(env,'room',['look','inventory'])
        obj.model=model;obj.worker=lambda *a:decision
        return obj,calls,actions

    def case(self,n):
        return dict(goal='put two x in shelf.',steps=[row('action '+str(i),'observation '+str(i)) for i in range(n)],
            task=dict(game_sha256='a'*64),skills=dict(exemplar=None,insight=None))

    def test_remaining_actions_not_reset_to_fifty(self):
        with TemporaryDirectory() as d:
            s,c,a=self.harness(d,dict(status='applied',action='look',state={},reason='test fixture'))
            r=s.branch(self.case(48),'bounded','F',Path('fixture'))
            self.assertEqual(len(a),2);self.assertEqual(r['suffix_steps'],2);self.assertEqual(r['logical_model_calls'],0)

    def test_decline_resumes_native_without_reentry(self):
        with TemporaryDirectory() as d:
            s,c,a=self.harness(d,dict(status='declined',state={},reason='test fixture'))
            r=s.branch(self.case(47),'decline','F',Path('fixture'))
            self.assertEqual(r['worker_calls'],1);self.assertEqual(r['logical_model_calls'],3);self.assertEqual(len(a),3)

    def test_error_resumes_native_and_is_counted(self):
        with TemporaryDirectory() as d:
            s,c,a=self.harness(d,dict(status='error',state={},reason='fixture error'))
            r=s.branch(self.case(49),'error','F',Path('fixture'))
            self.assertEqual(r['policy_errors'],1);self.assertEqual(r['logical_model_calls'],1)

    def test_development_decline_does_not_buy_native_success(self):
        with TemporaryDirectory() as d:
            s,c,a=self.harness(d,dict(status='declined',state={},reason='fixture'))
            r=s.branch(self.case(16),'development','F',Path('fixture'),development=True)
            self.assertEqual(c,[]);self.assertFalse(r['won']);self.assertEqual(r['suffix_steps'],0)

    def test_replan_charges_one_extra_call_and_equal_state(self):
        with TemporaryDirectory() as d:
            s,c,a=self.harness(d,dict(status='declined',state={},reason='fixture'))
            case=self.case(49)
            g=s.branch(case,'G','G');r=s.branch(case,'R','R');f=s.branch(case,'F','F',Path('fixture'))
            self.assertEqual({x['start_sha256'] for x in (g,r,f)},{g['start_sha256']})
            self.assertEqual(r['logical_model_calls'],2);self.assertEqual(g['logical_model_calls'],1)
            self.assertEqual(f['logical_model_calls'],1)

    def test_real_development_anchors_remain_exposed(self):
        eps={e['sequence']:e for e in C.A.read(C.SOURCE)}
        for n,k in ((41,16),(12,26),(107,24)):
            case=C.archived_case(eps[n],k)
            self.assertEqual(C.retake_anchors(case['goal'],case['steps'])[0],k)
        self.assertEqual(len([e for e in eps.values() if not e['won']]),7)


if __name__=='__main__': unittest.main()
