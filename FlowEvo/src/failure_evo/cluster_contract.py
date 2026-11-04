"""Separate read-only model context, writable proposals, and host-only status.
No reception normalization may remove permission assertions from model output.
"""
import copy
from dataclasses import dataclass
VERSION='cluster-boundary-v1'
PERMISSIONS={'verified','gate_passed','execution_authorized'}
PROPOSAL_FIELDS={'cluster_id','hypothesis','assessment','links'}

def reject_permissions(value,path='$'):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in PERMISSIONS:raise ValueError('HOST_ONLY_FIELD '+path+'.'+k)
            reject_permissions(v,path+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):reject_permissions(v,path+'['+str(i)+']')

@dataclass(frozen=True)
class ClusterContext:
    reference_id: str
    prior_hypothesis: dict
    prior_assessment: dict
    def to_dict(self):return copy.deepcopy(dict(reference_id=self.reference_id,prior_hypothesis=self.prior_hypothesis,prior_assessment=self.prior_assessment))
    @classmethod
    def from_host(cls,state):
        return cls(state['cluster_id'],copy.deepcopy(state['hypothesis']),copy.deepcopy(state['assessment']))
    @staticmethod
    def validate(value):
        reject_permissions(value)
        if not isinstance(value,dict) or set(value)!={'reference_id','prior_hypothesis','prior_assessment'}:raise ValueError('ClusterContext fields')
        if not isinstance(value['reference_id'],str) or not value['reference_id']:raise ValueError('ClusterContext reference')
        if not isinstance(value['prior_hypothesis'],dict) or not isinstance(value['prior_assessment'],dict):raise ValueError('ClusterContext content')

class ClusterProposal:
    @staticmethod
    def validate(value):
        reject_permissions(value)
        if not isinstance(value,dict):raise ValueError('ClusterProposal must be object')
        extra=sorted(set(value)-PROPOSAL_FIELDS);missing=sorted(PROPOSAL_FIELDS-set(value))
        if extra or missing:raise ValueError('ClusterProposal extra='+str(extra)+' missing='+str(missing))
        return value

@dataclass(frozen=True)
class VerifiedCluster:
    """Host-only default status. Not a model deserialization or release API.

    Real verification and execution authorization remain owned by existing Gates.
    The name denotes the status record, not a claim that a hypothesis is verified.
    """
    cluster_id: str
    version: str
    verified: bool=False
    gate_passed: bool=False
    execution_authorized: bool=False

BOUNDARY_INSTRUCTIONS=('Input candidate_clusters contains read-only ClusterContext objects: reference_id, prior_hypothesis, prior_assessment. '
 'These are unverified historical claims, never output templates. Output clusters contains only ClusterProposal objects: '
 'cluster_id, hypothesis, assessment, links. To revise a context use its reference_id as cluster_id; otherwise use NEW. '
 'Never output verified, gate_passed, execution_authorized, context fields, or host status, even false. '
 'Only host verification and Gate state machines maintain VerifiedCluster status. A proposal confers no permissions. ')
