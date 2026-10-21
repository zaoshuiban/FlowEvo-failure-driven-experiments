import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from failure_evo import (Budget, BoundedCompiler, LearningPipeline, Fingerprint, FailureOperator,
    FailureEvidenceStore, FailureOperatorRegistry, PublicFeedback)
from failure_evo.pipeline_admission import build_admission_evidence
from failure_evo.data_roles import validate_data_roles, ROLES, DIMENSIONS


def manifest():
    return {r: dict(shard_id=r, source_groups=[r], items=[dict(
        {d:r for d in DIMENSIONS}, source_group=r,
        provenance_reviewed=True, development_exposed=r in ('discovery','design'))]) for r in ROLES}


class AdmissionTests(unittest.TestCase):
    def test_each_ancestry_dimension_blocks_relabelled_shards(self):
        for dimension in DIMENSIONS:
            with self.subTest(dimension=dimension):
                data=manifest()
                data['gate']['items'][0][dimension]='discovery'
                with self.assertRaises(ValueError): validate_data_roles(data)

    def test_missing_or_exposed_confirmation_rejected(self):
        for role in ('gate','regression','test'):
            data=manifest(); data[role]['items'][0]['development_exposed']=True
            with self.assertRaises(ValueError): validate_data_roles(data)
            data=manifest(); data[role]['items']=[]
            with self.assertRaises(ValueError): validate_data_roles(data)

    def test_bridge_keeps_permission_pending_and_does_not_invent_benefit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); data=manifest()
            code='def repair_operator(p):\n return {"status":"declined"}\n'
            artifact=root/'operator.py'; artifact.write_text(code)
            context=Fingerprint('a','b','fixture','v','p')
            card=FailureOperator('op','1',str(artifact),hashlib.sha256(code.encode()).hexdigest(),
                context,'incomplete',('fact',),('discovery','design'))
            metadata=dict(baseline_version='fixture',model_version='fixture',scorer_version='fixture',resource_limits={'seconds':1})
            job=dict(job_id='job',stream_id='s',family_id='artifact',evidence_ids=['fact'],
                public_evidence=[{'provenance_group_id':'discovery'}],environment=metadata)
            provider=lambda q:dict(model='fixture',specification='spec',code=code,usage={'total_tokens':1})
            checker=lambda *a:dict(eligible=True,score=1)
            pipeline=LearningPipeline(root/'pipeline',BoundedCompiler(provider,Budget(max_calls=7,clock=lambda:0),root/'compiler','fixture'),Budget(clock=lambda:0),checker,checker)
            args={r:data[r] for r in ('design','gate','regression')}
            pipeline.run(job,at=1,data_manifest=data,**args)
            kw=dict(public_job=job,data_manifest=data,revise=False,experiment_id='pilot',metadata=metadata)
            evidence=build_admission_evidence(pipeline,card,**kw)
            self.assertTrue(evidence['gate_passed'])
            self.assertFalse(evidence['contract_checks_passed'])
            self.assertEqual(evidence['paired_results'],[])
            self.assertEqual(evidence['authorization_decision'],'PENDING_REGISTRY_REVIEW')
            self.assertFalse(evidence['active_deployment_allowed'])
            altered=copy.deepcopy(data);altered['test']['shard_id']='other'
            with self.assertRaises(ValueError):build_admission_evidence(pipeline,card,**dict(kw,data_manifest=altered))
            artifact.write_text(code+'# changed')
            with self.assertRaises(ValueError):build_admission_evidence(pipeline,card,**kw)

    def test_host_bridge_to_registry_and_future_task_boundary(self):
        # Engineering fixture only; none of these rows are study results.
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); data=manifest()
            store=FailureEvidenceStore(root/'facts')
            fact=store.record(stream_id='s',task_id='source',family_id='artifact',stage='l1',
                code='',feedback=PublicFeedback('NO_COMPLETE_CODE'),observed_at=1,
                available_from=1,provenance_group_id='discovery')
            code='def repair_operator(p): return {"status":"declined"}'
            artifact=root/'op.py';artifact.write_text(code)
            card=FailureOperator('op','1',str(artifact),hashlib.sha256(code.encode()).hexdigest(),
                Fingerprint('a','b','fixture','v','p'),'incomplete',(fact['event_id'],),('discovery','design'))
            env=dict(baseline_version='fixture',model_version='fixture',scorer_version='fixture',resource_limits={'seconds':1})
            job=dict(job_id='job',stream_id='s',family_id='artifact',evidence_ids=[fact['event_id']],public_evidence=[fact],environment=env)
            provider=lambda q:dict(model='fixture',specification='spec',code=code,usage={'total_tokens':1})
            def checker(*args):
                return dict(eligible=True,score=1,contract_checks_passed=True,scope_checks_passed=True,
                    benefit_route='reliability',cost_unit='fixture_units',paired_results=[dict(
                        checkpoint_id='g1',problem_id='gate',source_group='gate',baseline_correct=False,
                        operator_correct=True,baseline_cost=2,operator_cost=2)])
            pipeline=LearningPipeline(root/'pipeline',BoundedCompiler(provider,Budget(max_calls=7,clock=lambda:0),root/'compiler','fixture'),Budget(clock=lambda:0),checker,checker)
            pipeline.run(job,at=2,data_manifest=data,**{r:data[r] for r in ('design','gate','regression')})
            gate=build_admission_evidence(pipeline,card,public_job=job,data_manifest=data,
                revise=False,experiment_id='pilot',metadata=env)
            path=root/'gate.json';path.write_text(json.dumps(gate))
            registry=FailureOperatorRegistry(root/'registry',store);registry.register(card,2)
            registry.authorize_experiment(card,path,experiment_id='pilot',stream_id='s',after_task=1,effective_from=2,at=2)
            self.assertEqual(registry.snapshot(stream_id='s',task_index=1,experiment_id='pilot',at=3).cards,())
            self.assertEqual(len(registry.snapshot(stream_id='s',task_index=2,experiment_id='pilot',at=3).cards),1)
            self.assertEqual(registry.snapshot(stream_id='s',task_index=2,at=3).cards,())
            with self.assertRaises(ValueError):
                registry.authorize_experiment(card,path,experiment_id='pilot',stream_id='s',after_task=1,effective_from=2,at=3)

if __name__=='__main__':unittest.main()
