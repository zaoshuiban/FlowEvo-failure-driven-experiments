"""Default-off scalar mathematical operators, executed from exact generated source."""
import ast,hashlib,json,time
from pathlib import Path
from .static_contract import exit_paths
from .contracts import fingerprint,canonical
from .evidence import EvidenceStore
from .autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask

VERSION='math-scalar-operator-v1'
ALLOWED_IMPORTS={'math','collections','itertools','functools','re','heapq','bisect','fractions','statistics','json'}
FORBIDDEN={'open','eval','exec','compile','getattr','setattr','delattr','globals','locals','vars','input','breakpoint','help','__import__'}

def validate_math_source(code):
    errors=[]
    if not isinstance(code,str) or not 1<=len(code.encode())<=65536:return dict(passed=False,errors=['SOURCE_SIZE'])
    try:tree=ast.parse(code)
    except SyntaxError:return dict(passed=False,errors=['SYNTAX'])
    if len(list(ast.walk(tree)))>12000:errors.append('AST_SIZE')
    entries=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='math_operator']
    if len(entries)!=1:errors.append('ENTRY')
    else:
        a=entries[0].args
        if len(a.args)+len(a.posonlyargs)!=1 or a.vararg or a.kwarg or a.kwonlyargs or a.defaults or entries[0].decorator_list or entries[0].returns or any(x.annotation for x in a.args+a.posonlyargs):errors.append('SIGNATURE')
    for n in tree.body:
        if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign,ast.Expr)):errors.append('TOP_LEVEL')
        if isinstance(n,ast.Expr) and not isinstance(n.value,ast.Constant):errors.append('TOP_LEVEL_EXECUTION')
        if isinstance(n,ast.Assign):
            try:ast.literal_eval(n.value)
            except (ValueError,TypeError):errors.append('TOP_LEVEL_EXECUTION')
    for n in ast.walk(tree):
        if isinstance(n,ast.Import) and any(a.name not in ALLOWED_IMPORTS for a in n.names):errors.append('IMPORT')
        if isinstance(n,ast.ImportFrom) and (n.level or n.module not in ALLOWED_IMPORTS or any(a.name.startswith('_') for a in n.names)):errors.append('IMPORT')
        if isinstance(n,ast.Name) and (n.id in FORBIDDEN or n.id.startswith('__')):errors.append('FORBIDDEN_NAME')
        if isinstance(n,ast.Attribute) and n.attr.startswith('_'):errors.append('PRIVATE_ATTRIBUTE')
        if isinstance(n,(ast.AsyncFunctionDef,ast.ClassDef,ast.Global,ast.Nonlocal)):errors.append('UNSUPPORTED_CAPABILITY')
        if isinstance(n,ast.FunctionDef) and (n.returns or any(a.annotation for a in n.args.args+n.args.posonlyargs+n.args.kwonlyargs) or n.decorator_list or n.args.defaults or n.args.kw_defaults and any(v is not None for v in n.args.kw_defaults)):errors.append('DEFINITION_EXECUTION')
    if entries:
        returns=[]
        def visit(n):
            if isinstance(n,(ast.FunctionDef,ast.Lambda)):return
            if isinstance(n,ast.Return):returns.append(n.value)
            for c in ast.iter_child_nodes(n):visit(c)
        for n in entries[0].body:visit(n)
        for n in returns:
            if not isinstance(n,ast.Dict) or any(not isinstance(k,ast.Constant) or not isinstance(k.value,str) for k in n.keys):errors.append('RETURN');continue
            pairs={k.value:v for k,v in zip(n.keys,n.values)};status=pairs.get('status')
            status=status.value if isinstance(status,ast.Constant) else None
            want={'status','answer'} if status=='APPLIED' else {'status','reason'}
            if status not in ('APPLIED','DECLINED','ERROR') or set(pairs)!=want:errors.append('RETURN')
        if not returns or exit_paths(entries[0].body)&{'NEXT','BREAK','CONTINUE','UNVERIFIED'}:errors.append('RETURN_PATH')
    return dict(passed=not errors,errors=sorted(set(errors)),source_sha256=hashlib.sha256(code.encode()).hexdigest(),protocol=VERSION,
                limitations='static permissions are not a proof of semantic applicability or absence of answer memorization')

class MathOperatorRunner:
    def __init__(self,backend,budget=None):
        if not isinstance(backend,FrozenLinuxBackend):raise TypeError('frozen actual Linux backend required')
        self.backend=backend;self.budget=budget
    def run(self,artifact,task,*,timeout=2):
        if not isinstance(task,PublicMathTask):raise TypeError('public task required')
        path=Path(artifact['source_path']);code=path.read_text();digest=hashlib.sha256(code.encode()).hexdigest()
        if digest!=artifact['code_sha256']:raise RuntimeError('operator code hash mismatch')
        check=validate_math_source(code)
        if not check['passed']:raise PermissionError('operator static safety rejected: '+','.join(check['errors']))
        started=time.monotonic()
        request=dict(mode='function',function='math_operator',args=[{'problem':task.problem}],timeout=timeout)
        if artifact.get('origin')=='GPT' and self.budget is None:raise PermissionError('real operator requires frozen tool budget')
        key=self.budget.tool(capability='math-operator',request_hash=fingerprint([digest,request])) if self.budget else None
        try:
            with self.backend(path) as worker:raw=worker.call(request)
        finally:
            if key is not None:self.budget.settle(key,tool_milliseconds=int((time.monotonic()-started)*1000))
        if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RuntimeError('math Worker infrastructure fault')
        value=raw.get('value')
        if raw['status']!='OK':value=dict(status='ERROR',reason=raw['status'])
        if not isinstance(value,dict) or value.get('status') not in ('APPLIED','DECLINED','ERROR'):
            value=dict(status='ERROR',reason='OUTPUT_CONTRACT')
        expected={'status','answer'} if value['status']=='APPLIED' else {'status','reason'}
        if set(value)!=expected or any(not isinstance(v,str) for v in value.values()) or len(canonical(value).encode())>4096 or (value['status']=='APPLIED' and not value['answer'].strip()):
            value=dict(status='ERROR',reason='OUTPUT_CONTRACT')
        return dict(value,operator_id=artifact['operator_id'],code_sha256=digest,
                    seconds=time.monotonic()-started,worker_status=raw['status'],gold_exposed=False,request_sha256=fingerprint(request))

class MathOperatorRegistry:
    def __init__(self,path):self.events=EvidenceStore(path)
    def shadow(self,artifact):
        self.events.append('MATH_SHADOW',artifact,time.time())
    def admit(self,artifact,validation,*,after_sequence):
        if validation.get('code_sha256')!=artifact['code_sha256'] or validation.get('gate_passed') is not True or validation.get('selected_before_gate') is not True:
            raise PermissionError('bound frozen source/design/gate validation required')
        journal=validation.get('journal')
        if not journal or not any(r['kind']=='GATE_DECISION' and r['payload']==validation for r in EvidenceStore(journal).records()):raise PermissionError('host Gate receipt required')
        receipts=EvidenceStore(journal).records()
        if not any(r['kind']=='DEVELOPMENT_REVIEW' and r['payload']['artifact']==artifact and r['payload']['development_passed'] for r in receipts):raise PermissionError('source/Design receipt required')
        if not any(r['kind']=='PRE_GATE_FREEZE' and r['payload']['code_sha256']==artifact['code_sha256'] for r in receipts):raise PermissionError('pre-Gate freeze required')
        if not any(r['kind']=='MATH_SHADOW' and r['payload']==artifact for r in self.events.records()):raise PermissionError('unknown generated artifact')
        self.events.append('MATH_EXPERIMENTAL',dict(artifact=artifact,validation=validation,effective_after=after_sequence),time.time())
    def suspend(self,code_sha256,reason):
        self.events.append('MATH_SUSPENDED',dict(code_sha256=code_sha256,reason=reason),time.time())
    def eligible(self,task,sequence):
        rows=self.events.records();suspended={r['payload']['code_sha256'] for r in rows if r['kind']=='MATH_SUSPENDED'}
        entries=[]
        for r in rows:
            if r['kind']!='MATH_EXPERIMENTAL':continue
            p=r['payload'];a=p['artifact']
            if a['code_sha256'] in suspended or sequence<=p['effective_after'] or task.task_id in a['excluded_task_ids']:continue
            entries.append(a)
        return sorted({a['code_sha256']:a for a in entries}.values(),key=lambda a:a['code_sha256'])

class FrozenMathLibrary:
    def __init__(self,registry,runner,*,engineering=False):self.registry=registry;self.runner=runner;self.engineering=engineering
    def run(self,task,*,sequence):
        rows=[]
        for a in self.registry.eligible(task,sequence):
            if a['origin']=='MOCK' and not self.engineering:raise PermissionError('Mock artifact cannot enter real task solving')
            result=self.runner.run(a,task);rows.append(result)
            if result['status']=='APPLIED':break
        return rows
