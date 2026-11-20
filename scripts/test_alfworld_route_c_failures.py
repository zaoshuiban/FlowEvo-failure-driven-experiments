"""Tests for diagnostic measurements; fixtures are not research observations."""
import copy
import unittest
from pathlib import Path
import audit_alfworld_route_c_failures as C


def step(action='go to cabinet 1',obs='You arrive at cabinet 1. The cabinet 1 is open. In it, you see nothing.',**kw):
    return dict(action=action,observation=obs,legal_before=kw.get('commands',[]),legal_after=kw.get('after',[]),model_output=kw.get('output'))


class AuditTests(unittest.TestCase):
    def test_original_parser_exact(self):
        p=C.parsed_action('Think: continue\nAct: look',['look','inventory'])
        self.assertEqual(p['stage'],'ACT_EXACT');self.assertFalse(p['different'])

    def test_real_silent_fallback(self):
        p=C.parsed_action('Think: place it here.\nAct: put towel 1 on countertop 1',['examine countertop 1','look'])
        self.assertEqual(p['actual'],'examine countertop 1');self.assertEqual(p['stage'],'FIRST_ADMISSIBLE_FALLBACK')
        self.assertTrue(p['different'])

    def test_think_substring_is_recorded(self):
        p=C.parsed_action('Think: maybe look.\nAct: invalid',['inventory','look'])
        self.assertEqual(p['stage'],'WHOLE_OUTPUT_SUBSTRING');self.assertEqual(p['actual'],'look')

    def test_prefix_invariance(self):
        seq=[step() for _ in range(12)]
        all_rows=C.signals('find an object','room',seq)
        for n in range(1,13):
            self.assertEqual(C.signals('find an object','room',seq[:n]),[r for r in all_rows if r['step']<=n])

    def test_receipt_change_not_duplicate(self):
        s=[step(),step(obs='You arrive at cabinet 1. The cabinet 1 is open. In it, you see a cup 1.')]
        self.assertEqual(C.signals('task','room',s),[])

    def test_open_and_arrival_share_contents(self):
        s=[step('open cabinet 1','You open the cabinet 1. The cabinet 1 is open. In it, you see nothing.'),step()]
        self.assertEqual(C.signals('task','room',s)[0]['signal'],'KNOWN_CONTENT_REVISIT')

    def test_no_effect_is_not_searched_contents(self):
        self.assertIsNone(C.search_location('go to cabinet 1','Nothing happens.'))

    def test_stagnation_needs_full_window(self):
        self.assertNotIn('REVISIT_STAGNATION_10',[r['signal'] for r in C.signals('x','x',[step()]*9)])
        self.assertIn('REVISIT_STAGNATION_10',[r['signal'] for r in C.signals('x','x',[step()]*10)])

    def test_progress_blocks_stagnation_signal(self):
        s=[step()]*9+[step('take cup 1 from cabinet 1','You pick up the cup 1 from the cabinet 1.')]
        self.assertNotIn('REVISIT_STAGNATION_10',[r['signal'] for r in C.signals('x','x',s)])

    def test_retake_is_only_a_signal(self):
        s=[step('move cup 1 to shelf 1','You move the cup 1 to the shelf 1.'),step('take cup 1 from shelf 1','You pick up the cup 1 from the shelf 1.')]
        f=C.signals('task','room',s)[0]
        self.assertEqual(f['signal'],'RETAKE_PREVIOUSLY_PLACED_OBJECT');self.assertIn('legitimate',f['availability'])

    def test_goal_processing_signal(self):
        s=[step('move mug 1 to microwave 1','You move the mug 1 to the microwave 1.',commands=['heat mug 1 with microwave 1'])]
        self.assertEqual(C.signals('heat some mug','room',s)[0]['signal'],'PROCESS_AVAILABLE_BEFORE_PUTDOWN')
        self.assertEqual(C.signals('put some mug','room',s),[])

    def test_success_processing_prevents_false_missing(self):
        s=[step('heat mug 1 with microwave 1','You heat the mug 1 using the microwave 1.'),step('move mug 1 to microwave 1','You move the mug 1 to the microwave 1.',commands=['heat mug 1 with microwave 1'])]
        self.assertNotIn('PROCESS_AVAILABLE_BEFORE_PUTDOWN',[r['signal'] for r in C.signals('heat mug','room',s)])

    def test_facts_whitelist_excludes_final_state(self):
        e=C.A.read(C.OUT/'episodes.private.json')[0];p=C.public_steps(e);old=copy.deepcopy(p)
        e['won']=not e['won'];e['steps'][-1]['feedback']['won']=True;e['hidden']='unknown'
        self.assertEqual(C.public_steps(e),old)
        self.assertEqual(set(p[0]),{'action','observation','legal_before','legal_after','model_output'})

    def test_all_original_responses_parse_to_actual_actions(self):
        count=0
        for e in C.A.read(C.OUT/'episodes.private.json'):
            for s in e['steps']:
                if s['requested']:
                    self.assertEqual(C.parsed_action(s['requested']['output'],s['legal_actions'])['actual'],s['feedback']['action']);count+=1
        self.assertEqual(count,838)

    def test_controls_exclude_failed_games(self):
        es=C.A.read(C.OUT/'episodes.private.json')
        for e in es:
            if not e['won']:
                selected=C.successes_for(e,es)
                self.assertEqual(len(selected),2)
                for x in selected:
                    target=next(t for t in es if t['task_id']==x['task_id'])
                    self.assertTrue(target['won']);self.assertEqual(target['task_type'],e['task_type'])

    def test_no_model_environment_or_candidate_execution(self):
        import ast
        t=ast.parse(Path(C.__file__).read_text());calls={n.func.attr for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls&{'initialize','step','generate','invoke','authorize','stage_request','failure_probe','recovery_probe'})


if __name__=='__main__':unittest.main()
