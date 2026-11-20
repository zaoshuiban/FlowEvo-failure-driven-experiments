"""Engineering assertions only; fake histories are not research observations."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import audit_alfworld_route_a_onpolicy as Q


def episode(actions=None,direct=1):
    actions=actions or [('move cup 1 to cabinet 1','Nothing happens.'),('open cabinet 1','opened'),('move cup 1 to cabinet 1','You move the cup 1 to the cabinet 1.')]
    steps=[]
    for i,(action,obs) in enumerate(actions,1):
        steps.append(dict(step=i,feedback=dict(action=action,observation=obs,commands=['open cabinet 1','look'],won=i==len(actions),done=i==len(actions)),
            decision=dict(source='L1_PATH' if i<=direct else 'MODEL',l1_executed=i<=direct,l2_injected=False,l3_injected=False),requested=None))
    return dict(goal='put a cup in cabinet.',initial=dict(observation='room',commands=['look']),steps=steps)


class P2Tests(unittest.TestCase):
    def test_project_exact_prefix_no_future(self):
        e=episode();e['steps'][2]['feedback']['observation']='PRIVATE_FUTURE';c=Q.project(e,1)
        self.assertEqual(len(c['history']),1);self.assertNotIn('PRIVATE_FUTURE',str(c));self.assertEqual(set(c),{'goal','observation','admissible_commands','history','state'})

    def test_missing_context_is_not_zero_opportunity(self):
        e=episode();del e['steps'][0]['feedback']['commands']
        with self.assertRaisesRegex(ValueError,'NOT_EVALUABLE'):Q.project(e,1)

    def test_goal_and_legality_are_actual_poststate(self):
        e=episode();self.assertEqual(Q.project(e,1)['admissible_commands'],e['steps'][0]['feedback']['commands'])

    def test_closed_container_signal(self):
        c=Q.project(episode(),1);self.assertEqual(Q.mechanism(c),'CLOSED_OPENABLE_DESTINATION_PLACEMENT')
        c['admissible_commands']=[];self.assertEqual(Q.mechanism(c),'PLACEMENT_OTHER_OR_UNRESOLVED')

    def test_open_signal_does_not_claim_repair(self):
        e=episode([('open cabinet 1','Nothing happens.'),('look','room')])
        self.assertEqual(Q.mechanism(Q.project(e,1)),'OTHER_NO_EFFECT')
        self.assertFalse(Q.suffix_outcome(e,1)['same_action_repair_verified'])

    def test_l1_final_failure_reaches_fallback(self):
        r=Q.bridge_audit(episode());self.assertEqual(r['trigger_anchors'],[1]);self.assertEqual(r['shadow_actions_selected'],0)

    def test_l1_internal_failure_overwritten(self):
        r=Q.bridge_audit(episode([('go to shelf 1','Nothing happens.'),('look','normal'),('look','normal')],direct=2))
        self.assertEqual(r['trigger_anchors'],[])

    def test_terminal_failure_has_no_callback(self):
        r=Q.bridge_audit(episode([('move cup 1 to cabinet 1','Nothing happens.')],direct=1));self.assertEqual(r['trigger_anchors'],[])

    def test_original_two_opportunity_cap(self):
        e=episode([('look','Nothing happens.')]*5,direct=0)
        self.assertEqual(Q.bridge_audit(e)['trigger_anchors'],[1,2])

    def test_plain_success_has_no_trigger(self):
        self.assertEqual(Q.bridge_audit(episode([('look','room'),('look','room')],0))['opportunities'],0)

    def test_native_repair_needs_same_effective_action(self):
        e=episode();r=Q.suffix_outcome(e,1);self.assertTrue(r['same_action_repair_verified']);self.assertEqual(r['steps_until_same_action_repair'],2)
        e['steps'][2]['feedback']['action']='look';self.assertFalse(Q.suffix_outcome(e,1)['same_action_repair_verified'])
        self.assertTrue(Q.suffix_outcome(e,1)['eventual_won'])

    def test_noeffect_retry_not_repair(self):
        e=episode();e['steps'][2]['feedback']['observation']='Nothing happens.';self.assertFalse(Q.suffix_outcome(e,1)['same_action_repair_verified'])

    def test_history_never_mutated(self):
        e=episode();old=copy.deepcopy(e);Q.bridge_audit(e);Q.project(e,1);Q.suffix_outcome(e,1);self.assertEqual(e,old)

    def test_unknown_ledger_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'b';Q.P.EvidenceStore(p).append('UNKNOWN',{},0)
            with self.assertRaises(Q.P.RunUnhealthy):Q.require_settled(p)

    def test_pending_ledger_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'b';Q.P.EvidenceStore(p).append('RESERVED',dict(request_id='x'),0)
            with self.assertRaises(Q.P.RunUnhealthy):Q.require_settled(p)

    def test_empty_denominator_not_success(self):
        b=dict(failures=[],episodes=[],not_evaluable=[dict(status='NOT_EVALUABLE')]);_,s=Q.summarize(b,[])
        self.assertEqual(s['recommendation'],'EVIDENCE_INSUFFICIENT');self.assertEqual(s['funnel'][-1]['events'],0)

    def test_repeated_states_not_independent_games(self):
        self.assertEqual(Q.count([dict(task_id='a'),dict(task_id='a')]),dict(events=2,games=1))

    def test_gate_only_api_surface(self):
        import ast
        tree=ast.parse(Path(Q.__file__).read_text());called={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(called & {'initialize','validate_source','stage_request','authorize','failure_probe','recovery_probe'})

    def test_native_baseline_export_is_integrity_checked(self):
        c=Q.cohort();self.assertEqual(len(c['episodes']),120);self.assertEqual(c['not_evaluable'],[])
        self.assertEqual(sum(e['won'] for e in c['episodes']),113)


if __name__=='__main__':unittest.main()
