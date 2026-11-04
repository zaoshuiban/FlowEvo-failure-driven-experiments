"""Opt-in symmetric engineering continuation. Host never rewrites model algorithms."""
import ast
import hashlib
import json
import symtable
import time
import os
from pathlib import Path
from .contracts import canonical, fingerprint
from .evidence import EvidenceStore
from .math_operators import validate_math_source, MathOperatorRunner
from .math_learning import CONTRACT
from code_math.no_gold import PublicMathTask
from code_math.private_math_scoring import answer_equal
from .autonomous_generation import DeepSeekCompilerAdapter, CODE_SCHEMA

VERSION = 'symmetric-math-engineering-repair-v2'
CONTRACT_EXTENSION = '''Engineering continuation of an existing model-generated artifact.
Preserve intended computation. Do not fit example answers or invent a new algorithm.
Disclose necessary computational changes in description; all semantic AST changes
are substantive unverified versions, never automatically formatting fixes.
Additionally implement def solve(parameters), returning a nonempty answer string,
and def map_parameters(problem), returning exactly status, parameters, reason.
Mapping status is MATCH, DECLINE or UNKNOWN; parameters is a dict and reason a string.
math_operator must use these generated components. Do not run tests at import time.
No trusted answers or private parameters are provided. Safely reject unsupported input.
Parsing a valid parameter object does not establish applicability. Verify the requested
mathematical quantity and required premises against the computation actually implemented.
Use UNKNOWN if a necessary premise cannot be established, with an empty parameters dict.
Do not treat an unsupported objective as a supported one merely because fields match.
'''

def digest(code):
    return hashlib.sha256(code.encode()).hexdigest()

def write_new(path, text):
    """Exclusive, durable artifact write. A partial file blocks reuse after a crash."""
    path = Path(path)
    with path.open('x', encoding='utf-8') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def receive_source(response, origin):
    """Do not execute partial content or reinterpret delivery failure as transport loss."""
    if not isinstance(response, dict):
        return 'RESPONSE_NOT_OBJECT'
    if response.get('finish_reason', 'stop' if origin=='MOCK' else None) != 'stop':
        return 'INCOMPLETE_DELIVERY'
    if response.get('delivery_status', 'PARSE_VALID' if origin=='MOCK' else None) != 'PARSE_VALID':
        return 'DELIVERY_CONTRACT_INVALID'
    if response.get('parse_status') or response.get('rejected_compile_output'):
        return 'DELIVERY_CONTRACT_INVALID'
    if not isinstance(response.get('code'), str) or not response['code'].strip():
        return 'MISSING_CODE'
    if len(response['code'].encode()) > 65536:
        return 'SOURCE_SIZE'
    if origin!='MOCK':
        raw=response.get('raw_response')
        if response.get('transport_status')!='RESPONSE_RECEIVED' or not isinstance(raw,dict) or fingerprint(raw)!=response.get('response_sha256'):
            return 'RESPONSE_PROVENANCE_MISMATCH'
        try:
            choices=raw['choices']
            if len(choices)!=1 or choices[0]['finish_reason']!='stop':return 'INCOMPLETE_DELIVERY'
            value=json.loads(choices[0]['message']['content'])
            if not isinstance(value,dict) or set(value)!=set(CODE_SCHEMA['required']) or value['code']!=response['code']:
                return 'SOURCE_PROVENANCE_MISMATCH'
            if any(not isinstance(value[k],str) or not value[k].strip() for k in CODE_SCHEMA['required']):
                return 'DELIVERY_CONTRACT_INVALID'
        except (KeyError,TypeError,ValueError,IndexError):
            return 'DELIVERY_CONTRACT_INVALID'
    return None

def diagnose(code):
    check = validate_math_source(code)
    details = []
    if not isinstance(code,str) or not 1<=len(code.encode())<=65536:
        return dict(static=check,details=[dict(kind='SOURCE_SIZE')],component_ready=False)
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return dict(static=check, details=[dict(kind='SYNTAX', line=e.lineno, message=e.msg)],component_ready=False)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Nonlocal, ast.Global, ast.ClassDef, ast.AsyncFunctionDef)):
            details.append(dict(kind='UNSUPPORTED_CAPABILITY', line=n.lineno,
                                node=type(n).__name__, text=ast.get_source_segment(code, n)))
    import builtins
    try:
        table = symtable.symtable(code, '<generated>', 'exec')
    except SyntaxError as e:
        return dict(static=check, details=details+[dict(kind='SYMBOL_TABLE_ERROR', message=e.msg)],component_ready=False)
    bound = {s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
    def visit(t):
        for s in t.get_symbols():
            if s.is_referenced() and s.is_global() and s.get_name() not in bound and s.get_name() not in vars(builtins):
                details.append(dict(kind='UNRESOLVED_GLOBAL', name=s.get_name(), scope=t.get_name()))
        for child in t.get_children():
            visit(child)
    visit(table)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in ('solve','map_parameters','math_operator'):
        if sum(isinstance(n,ast.FunctionDef) and n.name==name for n in tree.body)>1:
            details.append(dict(kind='DUPLICATE_ENTRY',name=name))
        if any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets) for n in tree.body):
            details.append(dict(kind='ENTRY_REBOUND',name=name))
    for name in ('solve', 'map_parameters'):
        n = functions.get(name)
        if n is None:
            details.append(dict(kind='MISSING_DIAGNOSTIC_ENTRY', name=name))
        elif len(n.args.args)+len(n.args.posonlyargs)!=1 or n.args.vararg or n.args.kwarg or n.args.kwonlyargs:
            details.append(dict(kind='DIAGNOSTIC_SIGNATURE', name=name))
    blockers={'MISSING_DIAGNOSTIC_ENTRY','DIAGNOSTIC_SIGNATURE','DUPLICATE_ENTRY','ENTRY_REBOUND','UNRESOLVED_GLOBAL'}
    return dict(static=check, details=details, static_only=True,
                component_ready=check['passed'] and not any(d['kind'] in blockers for d in details))

def _semantic_ast(code):
    tree = ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n,(ast.Module,ast.FunctionDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) and isinstance(n.body[0].value.value,str):
            n.body.pop(0)
    return tree

def version_change(old,new):
    result=dict(parent_sha256=digest(old),code_sha256=digest(new),equivalence_proven=False,validation_inherited=False)
    if old==new:
        return dict(result,classification='IDENTICAL',equivalence_proven=True,changed_functions=[])
    try:
        a,b=_semantic_ast(old),_semantic_ast(new)
    except SyntaxError:
        return dict(result,classification='SUBSTANTIVE_OR_UNRESOLVED',changed_functions=None)
    if ast.dump(a)==ast.dump(b):
        return dict(result,classification='FORMAT_OR_DOCSTRING_ONLY',equivalence_proven=True,changed_functions=[])
    fa={n.name:ast.dump(n) for n in a.body if isinstance(n,ast.FunctionDef)}
    fb={n.name:ast.dump(n) for n in b.body if isinstance(n,ast.FunctionDef)}
    return dict(result,classification='SUBSTANTIVE_OR_UNRESOLVED',changed_functions=sorted(k for k in fa.keys()|fb.keys() if fa.get(k)!=fb.get(k)))

def engineering_request(code,public_tasks):
    tasks=[PublicMathTask.parse(t) for t in public_tasks]
    return dict(protocol=VERSION,code=code,code_sha256=digest(code),diagnostics=diagnose(code),
                public_problems=[t.problem for t in tasks],contract=CONTRACT+CONTRACT_EXTENSION,gold_exposed=False)

class EngineeringRepairAdapter(DeepSeekCompilerAdapter):
    protocol=VERSION
    def preflight(self,request):
        self._authorize()
        if request['phase']!='revision':raise PermissionError('engineering revision only')
        payload=engineering_request(request['code'],request['public_tasks'])
        if payload!=request['engineering']:raise PermissionError('engineering projection mismatch')
        wire=dict(model=self.model,messages=[dict(role='system',content=payload['contract']+'\nRequired JSON schema: '+canonical(CODE_SCHEMA)),
                  dict(role='user',content=canonical({k:v for k,v in payload.items() if k!='contract'}))],
                  max_tokens=request['max_tokens'],temperature=0,thinking={'type':'disabled'},reasoning_effort='none',
                  response_format={'type':'json_object'},stream=False)
        if len(canonical(wire).encode())+256>self.max_wire_input_upper:raise ValueError('wire input ceiling')
        return wire

class EngineeringRepairSession:
    """One durable attempt including unknown and rejected delivery; provider owns ledger."""
    def __init__(self,path):
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.events=EvidenceStore(self.path/'repair.jsonl')
    def repair(self,code,public_tasks,sender,*,origin):
        request=engineering_request(code,public_tasks)
        write_new(self.path/'ATTEMPT_STARTED.json',canonical(dict(parent_sha256=digest(code),protocol=VERSION,origin=origin)))
        write_new(self.path/'original.py',code)
        write_new(self.path/'request.json',canonical(request))
        self.events.append('ENGINEERING_REQUEST_STARTED',dict(request_sha256=fingerprint(request),origin=origin),time.time())
        try:
            response=sender(request)
        except BaseException as e:
            self.events.append('SEND_UNRESOLVED_OR_REJECTED',dict(error_type=type(e).__name__,reason=str(e),
                transport_state_authority='provider and budget journals; do not infer',retry=False),time.time())
            raise
        write_new(self.path/'response.json',canonical(response))
        self.events.append('MODEL_RESPONSE_RECEIVED',dict(response_sha256=fingerprint(response)),time.time())
        rejection=receive_source(response,origin)
        if rejection:
            self.events.append('DELIVERY_REJECTED',dict(reason=rejection,transport_unknown=False),time.time())
            return dict(status='DELIVERY_REJECTED',reason=rejection)
        new=response['code']
        write_new(self.path/'revised.py',new)
        review=dict(status='RECEIVED_UNVERIFIED',origin=origin,change=version_change(code,new),diagnostic=diagnose(new),source_path=str((self.path/'revised.py').resolve()))
        write_new(self.path/'review.json',canonical(review))
        self.events.append('VERSION_REVIEW',review,time.time())
        return review

class ComponentValidation:
    def __init__(self,backend,budget,journal):
        self.backend,self.budget=backend,budget
        self.runner=MathOperatorRunner(backend,budget);self.events=EvidenceStore(journal)
    def call(self,artifact,function,args):
        if function not in ('solve','map_parameters'):raise PermissionError('component entry allowlist')
        path=Path(artifact['source_path'])
        if digest(path.read_text())!=artifact['code_sha256']:raise PermissionError('source hash mismatch')
        if not diagnose(path.read_text())['component_ready']:raise PermissionError('component contract rejection')
        req=dict(mode='function',function=function,args=args,timeout=2)
        key=self.budget.tool(capability='math-engineering-component',request_hash=fingerprint([artifact['code_sha256'],req]))
        start=time.monotonic()
        try:
            with self.backend(path) as worker:raw=worker.call(req)
        except BaseException as exc:
            self.events.append('COMPONENT_EXECUTION_INTERRUPTED',dict(code_sha256=artifact['code_sha256'],request=req,error_type=type(exc).__name__),time.time())
            raise
        finally:
            self.budget.settle(key,tool_milliseconds=int((time.monotonic()-start)*1000))
        self.events.append('COMPONENT_EXECUTED',dict(code_sha256=artifact['code_sha256'],request=req,raw=raw),time.time())
        if not isinstance(raw,dict) or 'status' not in raw or raw.get('status') in ('WORKER_ERROR','EVALUATOR_ERROR'):raise RuntimeError('Worker infrastructure fault')
        return raw
    def evaluate(self,artifact,cases,role):
        if role not in ('Source','Design','Gate'):raise ValueError('unknown role')
        # Validate the entire set before spending tools or allowing partial grading.
        if not isinstance(cases,list) or not cases:raise ValueError('nonempty cases required')
        ids=set();problems=set()
        for c in cases:
            PublicMathTask(c['task_id'],c['problem'])
            if c.get('review_status')!='INDEPENDENT_VERIFIED' or type(c.get('supported')) is not bool:
                raise PermissionError('typed independent review required')
            if not isinstance(c.get('parameters'),dict) or c['supported'] and (not isinstance(c.get('answer'),str) or not c['answer'].strip()):
                raise ValueError('invalid private reference')
            if c['task_id'] in ids or ' '.join(c['problem'].split()) in problems:raise ValueError('duplicate validation case')
            ids.add(c['task_id']);problems.add(' '.join(c['problem'].split()))
        prior=[r['payload'] for r in self.events.records() if r['kind']=='PRIVATE_COMPONENT_VALIDATION' and r['payload']['code_sha256']==artifact['code_sha256']]
        if any(r.get('protocol')!=VERSION for r in prior):raise PermissionError('new validation namespace required')
        if any(r['role']==role for r in prior):raise PermissionError('validation role already consumed')
        if any(ids.intersection(r['task_ids']) or problems.intersection(r['problems_normalized']) for r in prior):raise PermissionError('validation role overlap')
        binding=fingerprint([artifact['code_sha256'],role])
        marker=self.events.path.parent/('validation-started-'+binding+'.json')
        write_new(marker,canonical(dict(role=role,code_sha256=artifact['code_sha256'],cases_sha256=fingerprint(cases))))
        rows=[]
        for c in cases:
            if c['review_status']!='INDEPENDENT_VERIFIED':raise PermissionError('independent review required')
            task=PublicMathTask(c['task_id'],c['problem'])
            mapping=self.call(artifact,'map_parameters',[task.problem]);v=mapping.get('value')
            valid=(mapping['status']=='OK' and isinstance(v,dict) and set(v)=={'status','parameters','reason'} and v['status'] in ('MATCH','DECLINE','UNKNOWN') and isinstance(v['parameters'],dict) and isinstance(v['reason'],str) and (v['status']=='MATCH' or v['parameters']=={}))
            computation=self.call(artifact,'solve',[c['parameters']]) if c['supported'] else None
            end=self.runner.run(artifact,task)
            comp_correct=bool(computation and computation['status']=='OK' and isinstance(computation.get('value'),str) and answer_equal(computation['value'],c['answer']))
            combined=end['status']=='APPLIED' and c['supported'] and answer_equal(end['answer'],c['answer'])
            rows.append(dict(task_id=c['task_id'],role=role,supported=c['supported'],mapping=mapping,mapping_valid=valid,
                parameter_correct=(fingerprint(v['parameters'])==fingerprint(c['parameters'])) if valid and c['supported'] and v['status']=='MATCH' else None,
                mapping_status=v['status'] if valid else 'ERROR',
                routing_consistent=valid and ((v['status']=='MATCH' and end['status']=='APPLIED') or (v['status'] in ('DECLINE','UNKNOWN') and end['status']=='DECLINED')),
                computation=computation,computation_correct=comp_correct if c['supported'] else None,end_to_end=end,combined_correct=combined,
                false_accept=not c['supported'] and end['status']=='APPLIED',correct_refusal=not c['supported'] and end['status']=='DECLINED'))
            row=rows[-1];failures=[]
            if not valid:failures.append('MAPPING_CONTRACT_ERROR')
            if row['parameter_correct'] is False:failures.append('PARAMETER_MISMATCH')
            if computation and computation['status']!='OK':failures.append('COMPUTATION_EXECUTION_ERROR')
            elif computation and not comp_correct:failures.append('COMPUTATION_MISMATCH')
            if end['status']=='ERROR':failures.append('END_TO_END_EXECUTION_ERROR')
            if not row['routing_consistent']:failures.append('ROUTING_INCONSISTENT')
            if row['false_accept']:failures.append('FALSE_ACCEPT')
            if c['supported'] and end['status']=='DECLINED':failures.append('SUPPORTED_INPUT_REFUSED')
            row['failure_categories']=failures
            self.events.append('PRIVATE_CASE_VALIDATED',dict(code_sha256=artifact['code_sha256'],row=rows[-1]),time.time())
        if digest(Path(artifact['source_path']).read_text())!=artifact['code_sha256']:raise PermissionError('source changed during validation')
        receipt=dict(protocol=VERSION,role=role,code_sha256=artifact['code_sha256'],cases_sha256=fingerprint(cases),task_ids=sorted(ids),problems_normalized=sorted(problems),rows=rows)
        self.events.append('PRIVATE_COMPONENT_VALIDATION',receipt,time.time());return receipt

def development_qualified(receipts):
    if len(receipts)!=2 or any(r.get('protocol')!=VERSION for r in receipts) or {r['role'] for r in receipts}!={'Source','Design'} or len({r['code_sha256'] for r in receipts})!=1:return False
    if set(receipts[0]['task_ids'])&set(receipts[1]['task_ids']) or set(receipts[0]['problems_normalized'])&set(receipts[1]['problems_normalized']):return False
    rows=[x for r in receipts for x in r['rows']]
    return bool(rows) and all(any(x['supported'] for x in r['rows']) for r in receipts) and any(not x['supported'] for x in rows) and all(x['mapping_valid'] and x['routing_consistent'] and (x['computation_correct'] and x['parameter_correct'] is True and x['combined_correct'] if x['supported'] else x['mapping_status']=='DECLINE' and x['correct_refusal'] and not x['false_accept']) for x in rows)


def freeze_for_gate(path, artifact, receipts, validation_journal):
    """Issue a readiness receipt, never Experimental or publication permission."""
    saved = EvidenceStore(validation_journal).records()
    for receipt in receipts:
        if not any(r['kind']=='PRIVATE_COMPONENT_VALIDATION' and r['payload']==receipt for r in saved):
            raise PermissionError('unbound validation receipt')
    if not development_qualified(receipts) or any(r['code_sha256']!=artifact['code_sha256'] for r in receipts):
        raise PermissionError('full source/development qualification required')
    if digest(Path(artifact['source_path']).read_text()) != artifact['code_sha256']:
        raise PermissionError('changed source invalidates validation')
    record=dict(protocol=VERSION, code_sha256=artifact['code_sha256'], receipts_sha256=fingerprint(receipts),
                validation_journal=str(Path(validation_journal).resolve()), status='READY_FOR_INDEPENDENT_GATE',
                experimental=False, excluded_task_ids=[r['task_id'] for v in receipts for r in v['rows']])
    write_new(path,canonical(record))
    return record
