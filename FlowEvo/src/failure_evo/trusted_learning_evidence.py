"""Opt-in host admission overlay. Never rewrites historical FailureEvidenceStore.

A caller must install reviewed grammar validators, pinned to a statement and code
hash. Saved legal_verified flags and model-produced claims are not validators.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
from .contracts import PublicTaskView, PublicFeedback, fingerprint, canonical
from .evidence import EvidenceStore
from .failure_events import structural_status

@dataclass(frozen=True)
class InputValidator:
    validator_id: str
    version: str
    task_id: str
    prompt_sha256: str
    source_path: str
    source_sha256: str
    scope: str
    basis: str
    check: object

    def verify(self, task, text):
        if not all((self.validator_id,self.version,self.scope,self.basis)) or not callable(self.check):
            raise ValueError('reviewed host validator required')
        if task['problem_id'] != self.task_id or fingerprint(task['prompt']) != self.prompt_sha256:
            raise ValueError('validator statement/task scope mismatch')
        if hashlib.sha256(Path(self.source_path).read_bytes()).hexdigest()!=self.source_sha256:
            raise ValueError('validator implementation changed')
        result=self.check(self.task_id,text)
        if not isinstance(result,dict) or type(result.get('valid')) is not bool:
            raise ValueError('validator must report explicit validity')
        return dict(result,validator_id=self.validator_id,version=self.version,scope=self.scope,basis=self.basis,
                    source_sha256=self.source_sha256,input_sha256=fingerprint(text))

class TrustedLearningEvidence:
    def __init__(self, store, path, validators):
        self.store=store;self.events=EvidenceStore(path);self.validators=dict(validators)

    def admit(self, checkpoint, *, at):
        allowed={'event_id','task','code','feedback','observed_at','lineage_id','legality_audit'}
        if set(checkpoint)-allowed or not (allowed-{'legality_audit'})<=set(checkpoint):
            raise ValueError('unknown or missing checkpoint fields')
        fact=next((x for x in self.store.visible(at) if x['event_id']==checkpoint['event_id']),None)
        if not fact or fact['synthetic']:raise ValueError('real visible failure required')
        task=checkpoint['task'];feedback=checkpoint['feedback']
        if set(task)-{'problem_id','prompt','starter_code','function_name','public_examples'}:
            raise ValueError('private/unknown task fields')
        if set(feedback)-{'status','visibility','cases','summary','tests_run','tests_passed'}:
            raise ValueError('private/unknown feedback fields')
        if (task['problem_id']!=fact['task_id'] or checkpoint['lineage_id']!=fact['provenance_group_id'] or
            checkpoint['observed_at']!=fact['observed_at'] or fact['available_from']>at or
            hashlib.sha256(checkpoint['code'].encode()).hexdigest()!=fact['candidate_sha256']):
            raise ValueError('time/source/code lineage mismatch')
        if feedback.get('visibility')!='public':raise ValueError('private feedback forbidden')
        cases=feedback.get('cases',[]);examples=task.get('public_examples',[])
        checks=[];reason='';valid=True
        validator=self.validators.get(fact['task_id'])
        if not validator:valid=False;reason='NO_REVIEWED_VALIDATOR'
        for case in cases+examples:
            if (set(case)-{'input','expected','actual','exception_class','visibility','legal_verified'} or
                case.get('visibility')!='public' or not isinstance(case.get('input'),str) or
                not isinstance(case.get('expected'),str)):
                raise ValueError('private/unknown or malformed public case')
            if validator:
                review=validator.verify(task,case['input']);checks.append(review)
                if not review['valid']:valid=False;reason='ILLEGAL_INPUT'
        kind='UNKNOWN';status=feedback.get('status')
        if not valid:kind='INPUT_OR_SCORING_ERROR' if reason=='ILLEGAL_INPUT' else 'UNKNOWN'
        elif status=='EVALUATOR_ERROR':kind='INFRASTRUCTURE_FAILURE'
        elif structural_status(checkpoint['code']) in ('NO_COMPLETE_CODE','COMPILE_ERROR'):
            kind='INCOMPLETE_DELIVERY'
        elif status in ('WRONG_ANSWER','RUNTIME_ERROR') and cases:
            if fact['observation_type']!='artifact' and status!=fact['verifier_status']:
                raise ValueError('feedback differs from historical fact')
            if any(c.get('actual')!=c['expected'] and 'actual' in c or c.get('exception_class') for c in cases):
                kind='PROGRAM_FAILURE'
        accepted=valid and kind in ('PROGRAM_FAILURE','INCOMPLETE_DELIVERY')
        receipt=dict(event_id=fact['event_id'],checkpoint_sha256=fingerprint(checkpoint),accepted=accepted,
                     classification=kind,reason=reason or kind,checks=checks,cutoff=at,
                     original_legality_claim=fact['input_legality_status'],root_cause_status='UNVERIFIED')
        self.events.append('ADMISSION_DECISION',receipt,at)
        if not accepted:
            self.events.append('EVIDENCE_ERRATUM',dict(receipt,original_event_unchanged=True),at)
            return None
        clean_cases=[dict(c,legal_verified=True) for c in cases]
        clean_task=dict(task,public_examples=[dict(c,legal_verified=True) for c in examples])
        projected=PublicFeedback.project(dict(feedback,cases=clean_cases))
        return dict(event_id=fact['event_id'],task=PublicTaskView.project(clean_task).to_dict(),code=checkpoint['code'],
            code_sha256=fact['candidate_sha256'],feedback=projected.to_dict(),observed_at=fact['observed_at'],
            available_from=fact['available_from'],lineage_id=fact['provenance_group_id'],stage=fact['stage'],
            finish_reason=fact['finish_reason'],structural_status=structural_status(checkpoint['code']),
            classification=kind,root_cause_status='UNVERIFIED',admission_sha256=fingerprint(receipt),
            legality=checks,repair_evidence_ids=fact['repair_evidence_ids'])

    def build(self, public_job, checkpoints, *, at):
        rows=[]
        for eid in public_job['evidence_ids']:
            row=self.admit(checkpoints[eid],at=at)
            if row is None:raise ValueError('untrusted discovery evidence: '+eid)
            rows.append(row)
        if not rows:raise ValueError('no trustworthy failure')
        return dict(public_job,discovery=dict(version='trusted-learning-evidence-v1',shared_cause='UNVERIFIED',evidence=rows))
