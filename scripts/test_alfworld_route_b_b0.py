"""No API: information isolation and native recovery bridge boundaries."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from alfworld_.route_b_information import packet,validate_packet,wire,balanced_packets
from alfworld_.route_b_runtime import RecoveryBridge
from alfworld_.learning_runtime import PolicyGenerator
from alfworld_.generator import AlfWorldStepOutput
from failure_evo.evidence import EvidenceStore
from failure_evo.run_health import RunUnhealthy

def cohort():
    episodes=[]
    for i in range(8):
        steps=[dict(step_ref='step_001',action='look',observation='Nothing happens.' if i>=4 else 'room',admissible_before=['look']),
               dict(step_ref='step_002',action='look',observation='PRIVATE_SUFFIX' if i>=4 else 'room',admissible_before=['look'])]
        episodes.append(dict(task_ref=f'task_{i}',goal=f'goal {i}',initial_observation='room',steps=steps,
            won=True,anchor=1 if i>=4 else None,markers=[1] if i>=4 else [],task=dict(task_type='fixture')))
    return dict(episodes=episodes,files={})

class ProjectionTests(unittest.TestCase):
    def test_shared_roster_no_failure_subset_leak_to_T(self):
        c=cohort();p={a:packet(c,a) for a in 'TSF'}
        self.assertEqual(p['T']['task_catalog'],p['F']['task_catalog'])
        self.assertEqual(p['S']['task_catalog'],p['F']['task_catalog'])
        self.assertEqual(p['T']['examples'],[])
        self.assertEqual(len(p['S']['examples']),4);self.assertEqual(len(p['F']['examples']),4)
        self.assertNotIn('PRIVATE_SUFFIX',str(p['F']))
    def test_suffix_private_fields_label_and_arm_tampering_rejected(self):
        c=cohort();base=packet(c,'F')
        for field in ('expert_plan','human_diagnosis','probe_location','candidate_code','gate_result'):
            p=copy.deepcopy(base);p[field]='private'
            with self.assertRaises(PermissionError):validate_packet(p,c,'F')
        p=copy.deepcopy(base);p['examples'][0]['steps']+=c['episodes'][4]['steps'][1:]
        with self.assertRaises(PermissionError):validate_packet(p,c,'F')
        with self.assertRaises(PermissionError):validate_packet(base,c,'S')
        p=copy.deepcopy(base);p['examples'][0]['observed_outcome']='SUCCESS'
        with self.assertRaises(PermissionError):validate_packet(p,c,'F')
    def test_source_drift_rejected(self):
        from failure_evo.math_stream import sha
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'raw';p.write_text('raw');c=cohort();c['files']={str(p):sha(p)}
            validate_packet(packet(c,'F'),c,'F');p.write_text('changed')
            with self.assertRaises(PermissionError):validate_packet(packet(c,'F'),c,'F')
    def test_wire_same_settings_and_system_only_user_evidence_differs(self):
        w=[wire(cohort(),a) for a in 'TSF']
        self.assertEqual(w[0]['messages'][0],w[1]['messages'][0]);self.assertEqual(w[1]['messages'][0],w[2]['messages'][0])
        for x in w:x.pop('messages')
        self.assertEqual(w[0],w[1]);self.assertEqual(w[1],w[2])
    def test_deterministic_quotas_no_overflow_resampling(self):
        c=cohort();a=balanced_packets(c);b=balanced_packets(c,max_wire_bytes=1)
        self.assertEqual(a['selection'],b['selection']);self.assertFalse(b['size_passed'])
        self.assertEqual(len(a['selection']['S']),len(a['selection']['F']))
        self.assertEqual(a,balanced_packets(c))

class BridgeTests(unittest.TestCase):
    def kwargs(self,obs='Nothing happens.',n=1):
        return dict(task_goal='goal',observation=obs,admissible_commands=['look'],
            action_history=['look']*n,observation_history=['Nothing happens.']*n,
            skill_context='native L2',policy_directives=['native L3'])
    def native(self):
        calls=[]
        def step(*args,**kwargs):calls.append((args,kwargs));return AlfWorldStepOutput(action='look',model_calls=1)
        return NS(step=step,calls=calls)
    def test_no_permission_preserves_every_native_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            native=self.native();p=PolicyGenerator(native,None,None,stream_id='s',experiment_id='NO_PERMISSIONS',
                task_id='t',sequence=1,events=EvidenceStore(Path(tmp)/'e'))
            b=RecoveryBridge(p);kw=self.kwargs();r=b.step(**kw)
            self.assertEqual(r.model_calls,1)
            self.assertEqual(native.calls[0][0],tuple(kw.values()))
            self.assertTrue(b.rows[0]['native_fallback'])
    def test_no_failure_does_not_run_policy(self):
        native=self.native();p=NS(native=native,states={},used=[],errors=set(),step=lambda **_:self.fail('must not run'))
        b=RecoveryBridge(p);kw=self.kwargs('ordinary feedback');b.step(**kw)
        self.assertEqual(native.calls,[((),kw)]);self.assertEqual(b.opportunities,0)
    def test_infrastructure_unknown_is_not_fallback(self):
        native=self.native()
        def bad(**_):raise RunUnhealthy('SEND_UNKNOWN')
        p=NS(native=native,states={},used=[],errors=set(),step=bad);b=RecoveryBridge(p)
        with self.assertRaisesRegex(RunUnhealthy,'SEND_UNKNOWN'):b.step(**self.kwargs())
        self.assertEqual(native.calls,[])
        with self.assertRaises(RunUnhealthy):b.finish(NS())
    def test_window_and_shared_episode_limit(self):
        native=self.native();p=NS(native=native,states={},used=[],errors=set())
        def apply(**kw):p.used.append('fixture');return AlfWorldStepOutput(action='look',model_calls=0)
        p.step=apply;b=RecoveryBridge(p,episode_limit=5,window=2)
        b.step(**self.kwargs(n=1));b.step(**self.kwargs('changed',2));b.step(**self.kwargs('changed',3))
        self.assertEqual(len(p.used),2);self.assertEqual(len(native.calls),1)
        with self.assertRaises(RunUnhealthy):b.step(**self.kwargs(n=5))
    def test_finalize_cannot_overwrite_native_L1(self):
        native=self.native();p=NS(native=native,states={},used=[],errors=set(),finalize=lambda trace:setattr(trace,'direct_use_count',999))
        t=NS(direct_use_count=5,actions=[]);RecoveryBridge(p).finish(t);self.assertEqual(t.direct_use_count,5)
    def test_selected_but_not_executed_is_not_actual_intervention(self):
        p=NS(native=self.native(),states={},used=[],errors=set(),finalize=lambda _:None)
        b=RecoveryBridge(p);b.rows=[dict(recovery_action_selected=True,environment_step=2,action='look',native_fallback=False)]
        value=b.finish(NS(actions=[]))
        self.assertEqual(value['selected_actions'],1);self.assertEqual(value['actual_actions'],0)
    def test_stale_receipt_not_reopened(self):
        native=self.native();p=NS(native=native,states={},used=[],errors=set(),step=lambda **kw:native.step(**kw))
        b=RecoveryBridge(p);b.step(**self.kwargs());b.step(**self.kwargs());self.assertEqual(b.opportunities,1)

if __name__=='__main__':unittest.main()
