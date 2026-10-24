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

# S19 opt-in strict host boundary. Existing tolerant historical projectors stay
# available for archived protocols; the new stream rejects, never guesses roles.
def _fields(value, allowed, required=()):
    if not isinstance(value,dict) or set(value)-set(allowed) or not set(required)<=set(value):
        raise ValueError('unknown/private/missing public field')

def _text(value):
    if not isinstance(value,str):raise ValueError('public scalar string required')
    return value

def strict_public_case(value, *, provenance=True):
    _fields(value,('input','expected','visibility','legal_verified','comparison','scorer','source','case_insensitive'),('input','expected','visibility','legal_verified'))
    if value['visibility']!='public' or value['legal_verified'] is not True:raise ValueError('trusted legal public case required')
    for k in ('input','expected','comparison','scorer'):
        if k in value:_text(value[k])
    if 'case_insensitive' in value and type(value['case_insensitive']) is not bool:raise ValueError('comparison flag must be boolean')
    if provenance:
        src=value.get('source');_fields(src,('kind','id','case_sha256'),('kind','id','case_sha256'))
        if src['kind'] not in ('public_statement','public_dataset','host_public_generator','engineering_fixture') or not _text(src['id']):raise ValueError('public source required')
        if src['case_sha256']!=fingerprint([value['input'],value['expected']]):raise ValueError('public source binding differs')
    return copy.deepcopy(value)

def strict_public_task(value):
    _fields(value,('problem_id','prompt','starter_code','function_name','public_examples'),('problem_id','prompt'))
    out={k:_text(v) for k,v in value.items() if k!='public_examples'}
    examples=value.get('public_examples',[])
    if not isinstance(examples,list):raise ValueError('public examples list required')
    out['public_examples']=[strict_public_case(c) for c in examples]
    return out

def strict_stream_task(value):
    _fields(value,('task_id','dataset','difficulty','task_public','public_cases','role'),('task_id','dataset','difficulty','task_public','public_cases'))
    out={k:_text(v) for k,v in value.items() if k not in ('task_public','public_cases')}
    out['task_public']=strict_public_task(value['task_public'])
    if out['task_public']['problem_id']!=out['task_id']:raise ValueError('task identity mismatch')
    if not isinstance(value['public_cases'],list) or not value['public_cases']:raise ValueError('public cases required')
    out['public_cases']=[strict_public_case(c) for c in value['public_cases']]
    return out

def strict_feedback(value):
    _fields(value,('status','summary','public_cases','visibility'),('status','summary','public_cases','visibility'))
    if value['visibility']!='public':raise ValueError('nonpublic feedback')
    cases=[]
    for c in value['public_cases']:
        _fields(c,('input','expected','actual','exception_class'),('input','expected'))
        for k,v in c.items():
            if v is not None:_text(v)
        cases.append(canonical(c))
    return PublicFeedback(_text(value['status']),_text(value['summary']),tuple(cases))

def atomic_json(path,value):
    import os,tempfile
    from pathlib import Path
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
