"""Bind routing authorization to frozen independent admission evidence."""
import hashlib,json,pathlib
from .evidence import EvidenceStore
class AdmissionRegistry:
    def __init__(self,path):self.events=EvidenceStore(path)
    @staticmethod
    def _check(card,gate,at):
        if gate.get('decision')!='ADMIT' or gate.get('evidence_role')!='FORMAL_ADMISSION':raise ValueError('experimental evidence cannot authorize active routing')
        if not all(gate.get(k) is True for k in ['frozen_before_evaluation','independent_validation','contract_checks_passed','scope_checks_passed','generation_data_isolated']):raise ValueError('independent gate incomplete')
        if gate.get('independent_source_groups',0)<2:raise ValueError('insufficient independent validation sources')
        if gate.get('artifact_sha256')!=card.artifact_sha256 or gate.get('fingerprint')!=card.evidence_fingerprint.to_dict() or gate.get('scope')!=card.evidence_scope:raise ValueError('gate scope or fingerprint differs')
        if gate.get('operator_id')!=card.operator_id or gate.get('version')!=card.version:raise ValueError('gate operator version differs')
        if at<gate['evaluated_at'] or at<card.published_at:raise ValueError('evidence not available yet')
        p=pathlib.Path(gate['promotion_policy_file'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=gate['promotion_policy_sha256']:raise ValueError('promotion policy changed')
    def admit(self,card,gate_path,at):
        path=pathlib.Path(gate_path);gate=json.loads(path.read_text());self._check(card,gate,at)
        if hashlib.sha256(pathlib.Path(card.artifact_path).read_bytes()).hexdigest()!=card.artifact_sha256:raise ValueError('artifact differs')
        return self.events.append('OPERATOR_ADMITTED',{'operator_id':card.operator_id,'version':card.version,'evidence_id':card.evidence_id,'gate_path':str(path.resolve()),'gate_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},at)
    def suspend(self,card,reason,at):return self.events.append('OPERATOR_SUSPENDED',{'operator_id':card.operator_id,'version':card.version,'reason':reason},at)
    def valid(self,card,context,at):
        try:
            entries=[r for r in self.events.visible(at) if r['payload']['operator_id']==card.operator_id and r['payload']['version']==card.version]
            if not entries or entries[-1]['kind']!='OPERATOR_ADMITTED' or context!=card.evidence_fingerprint:return False
            row=entries[-1]['payload'];p=pathlib.Path(row['gate_path'])
            if row['evidence_id']!=card.evidence_id or hashlib.sha256(p.read_bytes()).hexdigest()!=row['gate_sha256']:return False
            self._check(card,json.loads(p.read_text()),at);return True
        except (ValueError,KeyError,OSError,TypeError):return False
