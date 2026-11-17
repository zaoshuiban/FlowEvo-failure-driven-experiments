"""A1b data tests. Handwritten records below are ENGINEERING_FIXTURES only."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from unittest.mock import patch
import unittest

from alfworld_.route_a_training_labels import (review, window_sample, compatible, entity,
                                             model_projection, context)
from failure_evo.math_stream import read, sha
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
import prepare_alfworld_route_a_training_checkpoints as study


def step(action,observation,commands=(),won=False,score=0):
    return dict(action=action,observation=observation,commands=list(commands),won=won,done=won,score=score)


def fixture(process=False,unheld=False):
    subject='apple 1' if unheld else 'potato 1'
    prefix=[step('take potato 1 from countertop 1','You pick up the potato 1 from the countertop 1.'),
            step('inventory','You are carrying: a potato 1.')]
    if process:prefix.append(step('heat potato 1 with microwave 1','You heat the potato 1 using the microwave 1.'))
    prefix.append(step('examine fridge 1','The fridge 1 is closed.',['open fridge 1']))
    failure=step('move '+subject+' to fridge 1','Nothing happens.',['open fridge 1'])
    opened=step('open fridge 1','You open the fridge 1. The fridge 1 is open.',
                ['move potato 1 to fridge 1'])
    moved=step(failure['action'],'Nothing happens.' if unheld else 'You move the potato 1 to the fridge 1.',won=not unheld,score=0 if unheld else 1)
    return dict(collection_mode='CONTROLLED_INTERVENTION',replay_verified=True,
                execution_receipt_sha256='ENGINEERING_FIXTURE',prefix=prefix,failure=failure,
                recovery_probe=[opened,moved],original_goal='put a hot potato in fridge.' if process else 'put a potato in fridge.')


class LabelTest(unittest.TestCase):
    def test_positive_requires_actual_progress_and_replay(self):
        f=fixture(); self.assertEqual(review(f)['label'],'MATCH')
        f['recovery_probe'][-1]['won']=False
        self.assertIsNone(review(f)['label'])
        f=fixture();f['replay_verified']=False
        self.assertIsNone(review(f)['label'])

    def test_no_fake_failure_without_execution(self):
        f=fixture();f['execution_receipt_sha256']=None
        self.assertIsNone(review(f)['label'])
        f=fixture();f['failure']['observation']='You move the potato 1 to the fridge 1.'
        self.assertIsNone(review(f)['label'])

    def test_processed_positive_and_missing_phase_are_distinct(self):
        f=fixture(process=True)
        self.assertEqual(review(f)['label'],'MATCH')
        f['prefix']=[s for s in f['prefix'] if not s['action'].startswith('heat ')]
        self.assertIsNone(review(f)['label'])

    def test_partial_history_is_declared_and_unknown(self):
        f=fixture(process=True);label=review(f);partial=window_sample(f,label)
        self.assertEqual(partial['label'],'UNKNOWN')
        self.assertFalse(partial['public_history_scope']['complete'])
        self.assertEqual(len(partial['candidate_context']['history']),2)
        self.assertNotIn('You heat',str(partial['candidate_context']))
        plain=fixture();self.assertIsNone(window_sample(plain,review(plain)))
        plain['failure']['commands'].append('move potato 1 to countertop 1')
        plain['prefix'][-1]['commands'].append('move potato 1 to countertop 1')
        self.assertEqual(window_sample(plain,review(plain))['label'],'MATCH')

    def test_definite_mechanical_negative(self):
        f=fixture(unheld=True)
        self.assertEqual(review(f)['label'],'DECLINE')
        f['prefix'][1]['observation']='You are carrying: a apple 1.'
        self.assertIsNone(review(f)['label'])

    def test_wrong_held_intermediate_action_not_called_error(self):
        f=fixture(unheld=True)
        f['prefix'][1]['observation']='You are carrying: a apple 1.'
        f['recovery_probe'][0]['commands']=['move apple 1 to fridge 1']
        f['recovery_probe'][1]['observation']='You move the apple 1 to the fridge 1.'
        self.assertIsNone(review(f)['label'])

    def test_category_and_instance_are_distinct(self):
        self.assertTrue(compatible(entity('safe'),entity('safe 1')))
        self.assertFalse(compatible(entity('safe 999'),entity('safe 1')))
        self.assertFalse(compatible(entity('safe'),entity('fridge 1')))

    def test_counterfactual_goal_never_treated_as_natural(self):
        f=fixture();f['collection_mode']='SYNTHETIC_COUNTERFACTUAL'
        self.assertIsNone(review(f)['label'])

    def test_rule_or_model_claim_cannot_supply_a_label(self):
        f=fixture();f['recovery_probe'][-1]['won']=False
        f.update(rule_decision='MATCH',S0='MATCH',model_claim='verified')
        self.assertIsNone(review(f)['label'])

    def test_model_view_excludes_probes_and_identity(self):
        f=fixture();label=review(f)
        row=dict(label,sample_id='s001',candidate_context=context(f['original_goal'],f['prefix']+[f['failure']]),
                 public_history_scope={'complete':True},private_path='/private/forbidden',probe=f['recovery_probe'])
        wire=model_projection(row)
        self.assertNotIn('private_path',str(wire))
        self.assertNotIn('recovery_probe',str(wire))
        self.assertNotIn('You open',str(wire))
        self.assertEqual(set(wire),{'sample_id','public_context','public_history_scope','label','label_rationale'})

    def test_game_and_protected_roles(self):
        p=dict(games=['old_source','independent'],trajectories=['gate_trajectory'],groups=['gate_group'])
        def task(game):return {'task':dict(game_sha256=game,trajectory_sha256='other',group='other')}
        for game in p['games']:
            with self.assertRaises(PermissionError):study.check_isolation([task(game)],p)
        with self.assertRaises(PermissionError):study.check_isolation([task('same'),task('same')],p)
        study.check_isolation([task('new_train'),task('new_val')],p)

    def test_budget_and_wrong_prefix_block(self):
        class Env:
            def step(self,action):raise AssertionError('should not execute')
        class Receipts:
            def step(self,*args,**kwargs):raise RunUnhealthy('source transition differs')
        p=study.ProbeSteps(Env(),{'commands':['look']},Receipts(),None,'fixture',0)
        with self.assertRaises(BudgetExhausted):p.step('look','setup')
        p.deadline=float('inf')
        with self.assertRaises(RunUnhealthy):p.step('look','prefix',expected={'action':'look'})

    def test_freeze_does_not_change_existing_labels(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'record.json';study.commit(p,{'label':'UNKNOWN'})
            before=p.read_bytes()
            with self.assertRaises(PermissionError):study.commit(p,{'label':'MATCH'})
            self.assertEqual(p.read_bytes(),before)

    def test_pending_environment_step_and_global_budget_stop(self):
        from run_alfworld_python_recovery_feedback import EnvironmentReceipts
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'environment.jsonl'
            ledger=EvidenceStore(path)
            ledger.append('STEP_STARTED',dict(index=1,branch='probe',scope='intervention'),time.time())
            with self.assertRaises(RunUnhealthy):EnvironmentReceipts(path,10)
        with TemporaryDirectory() as tmp:
            ledger=EnvironmentReceipts(Path(tmp)/'environment.jsonl',0)
            with self.assertRaises(BudgetExhausted):ledger.step(None,'look',branch='probe',scope='intervention')

    def test_interrupted_branch_cannot_be_automatically_replayed(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            EvidenceStore(root/'probe.jsonl').append('BRANCH_STARTED',{'key':'pending'},time.time())
            with patch.object(study,'verify',return_value=({},{})):
                with self.assertRaises(RunUnhealthy):study.probe(root)

    def test_environment_and_source_hash_drift_block_before_execution(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); root.chmod(0o700)
            study.commit(root/'selection.private.json',{'tasks':[]})
            study.commit(root/'discovery.private.json',{'protected':{'games':[],'groups':[],'trajectories':[]}})
            source=root/'source.py'; source.write_text('# frozen')
            plan=dict(version=study.VERSION,limits=study.LIMITS,selection_sha256=sha(root/'selection.private.json'),
                      files={str(source):sha(source)},code_sha256={},data_root='ENGINEERING_FIXTURE',environment={'version':1})
            study.commit(root/'protocol.json',plan)
            with patch.object(study,'environment_manifest',return_value={'version':2}):
                with self.assertRaises(PermissionError):study.verify(root)
            source.write_text('# mutated')
            with patch.object(study,'environment_manifest',return_value={'version':1}):
                with self.assertRaises(PermissionError):study.verify(root)


class CollectedRealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=study.ROOT/'runs/alfworld_route_a_a1b_collection_20261113_01'

    def test_real_textworld_receipts_and_replay(self):
        plan,selection=study.verify(self.root,audit_only=True)
        events=study.records(self.root/'probe.jsonl')
        transitions=[r for r in events if r['kind']=='TRANSITION']
        self.assertTrue(transitions)
        for file in (self.root/'branches').glob('*.private.json'):
            b=read(file)
            if b['status']!='COLLECTED':continue
            self.assertEqual(b['failure']['observation'],'Nothing happens.')
            self.assertTrue(b['replay_verified'])
            steps=b['prefix']+[b['failure']]+b['recovery_probe']
            raw=[r for r in transitions if r['payload']['branch']==b['branch']]
            replay=[r for r in transitions if r['payload']['branch']==b['branch']+'/verification']
            self.assertEqual([r['payload']['after'] for r in raw],steps)
            self.assertEqual([r['payload']['after'] for r in replay],steps)
            self.assertLessEqual(len(steps),50)
        summary=read(self.root/'probe_summary.json')
        self.assertEqual(len(transitions),summary['total_environment_steps'])
        self.assertLessEqual(len(transitions),plan['limits']['total_environment_steps'])
        self.assertEqual(summary['paid_requests'],0)

    def test_independent_and_historical_games_not_used(self):
        _,selected=study.verify(self.root,audit_only=True)
        p=read(self.root/'discovery.private.json')['protected']
        study.check_isolation(selected['tasks'],p)
        self.assertFalse(set(r['task']['scene'] for r in selected['tasks']) & set(p['scenes']))

    def test_review_and_data_are_frozen_consistently(self):
        dataset=read(self.root/'dataset.json')
        self.assertEqual(sha(self.root/dataset['review_file']),dataset['review_sha256'])
        groups={}
        for role in ('TRAIN','TRAIN_VALIDATION'):
            rows=read(self.root/(role.lower()+'.private.json'))
            groups[role]={r['game_sha256'] for r in rows}
            self.assertTrue(all(r['collection_mode']=='CONTROLLED_INTERVENTION' for r in rows))
            self.assertEqual([model_projection(r) for r in rows],read(self.root/(role.lower()+'_model_view.private.json')))
            for row in rows:
                if row['label']=='UNKNOWN':self.assertFalse(row['public_history_scope']['complete'])
        self.assertFalse(groups['TRAIN']&groups['TRAIN_VALIDATION'])

    def test_grouping_amendment_does_not_relabel_or_allow_execution(self):
        with self.assertRaises(PermissionError):study.verify(self.root)
        old=read(self.root/'review.private.json');new=read(self.root/'review_grouped.private.json')
        def without_group(rows):
            return [{k:v for k,v in r.items() if k!='physical_state_group_id'} for r in rows]
        for key in ('samples','unresolved'):
            self.assertEqual(without_group(old[key]),without_group(new[key]))
        groups={}
        for sample in new['samples']:
            branch=read(self.root/'branches'/(sample['source_key']+'.private.json'))
            key=fingerprint([branch['task']['game_sha256'],branch['prefix']])
            self.assertEqual(key,sample['physical_state_group_id'])
            groups.setdefault(key,set()).add(sample['role'])
        self.assertTrue(all(len(roles)==1 for roles in groups.values()))

    def test_missing_validation_unknown_is_not_ready(self):
        d=read(self.root/'dataset.json')
        self.assertEqual(d['status'],'PARTIAL_COVERAGE')
        self.assertEqual(d['coverage']['TRAIN_VALIDATION']['UNKNOWN']['games'],0)
        self.assertFalse(d['A3_ready'])


if __name__=='__main__':unittest.main()
