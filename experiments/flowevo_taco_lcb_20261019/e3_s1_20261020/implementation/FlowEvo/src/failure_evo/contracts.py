"""Explicit public/private boundary and immutable execution contracts."""
from dataclasses import dataclass,asdict
import copy,hashlib,json

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

@dataclass(frozen=True)
class PublicTaskView:
    problem_id:str
    prompt:str
    starter_code:str=''
    function_name:str=''
    public_examples:tuple=()

    @classmethod
    def project(cls,raw):
        examples=[]
        for c in raw.get('public_examples',[]):
            if c.get('visibility')!='public' or c.get('legal_verified') is not True:continue
            examples.append(canonical({'input':c['input'],'expected':c['expected']}))
        return cls(str(raw.get('problem_id',raw.get('task_id',''))),str(raw['prompt']),str(raw.get('starter_code') or ''),str(raw.get('function_name') or ''),tuple(examples))

    def to_dict(self):
        d=asdict(self);d['public_examples']=[json.loads(x) for x in self.public_examples];return d

@dataclass(frozen=True)
class PublicFeedback:
    status:str
    summary:str=''
    public_cases:tuple=()
    visibility:str='public'

    @classmethod
    def project(cls,raw):
        if raw.get('visibility')!='public':return cls('PRIVATE_RESULT_WITHHELD')
        cases=[]
        for c in raw.get('cases',[]):
            if c.get('visibility')=='public' and c.get('legal_verified') is True:
                cases.append(canonical({k:copy.deepcopy(c[k]) for k in ['input','expected','actual','exception_class'] if k in c}))
        allowed={'PUBLIC_PASS','WRONG_ANSWER','RUNTIME_ERROR','TIME_LIMIT','COMPILE_ERROR','NO_COMPLETE_CODE','UNKNOWN','BUDGET_EXHAUSTED','EVALUATOR_ERROR'}
        status=raw.get('status','UNKNOWN')
        if status not in allowed:status='UNKNOWN'
        # Do not copy arbitrary raw feedback text containing a hidden-case preview.
        messages={'WRONG_ANSWER':'Wrong answer on audited public checks.','PUBLIC_PASS':'Audited public checks passed; hidden correctness unknown.',
                  'TIME_LIMIT':'Time limit on an audited public check.','RUNTIME_ERROR':'Runtime exception on an audited public check.',
                  'COMPILE_ERROR':'Program does not compile.','NO_COMPLETE_CODE':'No complete program was produced.',
                  'UNKNOWN':'Public evidence is insufficient.','EVALUATOR_ERROR':'Public checker error; do not infer a program defect.'}
        return cls(status,messages.get(status,''),tuple(cases))

    def to_dict(self):return {'status':self.status,'summary':self.summary,'public_cases':[json.loads(x) for x in self.public_cases],'visibility':'public'}

@dataclass(frozen=True)
class Fingerprint:
    baseline:str
    scorer:str
    model:str
    dependencies:str
    protocol:str
    def to_dict(self):return asdict(self)

@dataclass(frozen=True)
class OperatorCard:
    operator_id:str
    version:str
    status:str
    artifact_path:str
    artifact_sha256:str
    evidence_fingerprint:Fingerprint
    published_at:float
    stages:tuple=('l3',)
    required_ast_names:tuple=()
    allowed_feedback:tuple=('WRONG_ANSWER','RUNTIME_ERROR','TIME_LIMIT')
    prompt_terms:tuple=()
    evidence_scope:str=''
    max_seconds:float=1.0
    evidence_id:str=''
    dependency_files:tuple=()  # (path, sha256) pairs

def public_schema():
    return {'version':'public_view_v1','task_allowlist':['problem_id','prompt','starter_code','function_name','public_examples'],
            'feedback_allowlist':['status','summary_from_canonical_map','public_cases'],
            'excluded':['input_output','hidden_tests','reference_solution','final_score','future_trace','private_failed_case','arbitrary_feedback_text'],
            'public_case_requirement':['visibility=public','legal_verified=true'],
            'note':'Visibility/legal flags are supplied by the trusted host controller, never by candidate code.'}
