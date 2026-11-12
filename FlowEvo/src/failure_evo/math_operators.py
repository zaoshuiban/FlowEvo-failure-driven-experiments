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

# Rule metadata describes the same predicates used for legacy admission.
STATIC_RULES = {
    'SOURCE_SIZE': ('Source must fit the 1 to 65,536 byte limit.', 'Deliver one bounded UTF-8 source file.'),
    'SOURCE_BOUND': ('Environment source must be a string within 65,536 bytes.', 'Deliver bounded Python source as a string.'),
    'SYNTAX': ('The source must parse as Python.', 'Correct the syntax before checking permissions.'),
    'AST_SIZE': ('The AST may contain at most 12,000 nodes.', 'Use a smaller implementation.'),
    'MATH_ENTRY': ('Exactly one math_operator function is required.', 'Define a single math_operator(context).'),
    'ENV_ENTRY': ('Exactly one environment_operator function is required.', 'Define a single environment_operator(context).'),
    'MATH_SIGNATURE': ('The entry point must have the frozen single-argument signature.', 'Use an undecorated function with one unannotated parameter and no defaults.'),
    'ENV_SIGNATURE': ('The environment entry point takes one ordinary positional parameter.', 'Use def environment_operator(context).'),
    'TOP_LEVEL': ('Only imports, ordinary functions, literal assignments and constant expressions are allowed at module scope.', 'Keep execution inside an ordinary function.'),
    'MODULE_ASSIGNMENT_LITERAL': ('Module-level assignments must have literal values.', 'Keep a literal at module scope and do the computation inside a function.'),
    'MODULE_EXPRESSION_CONSTANT': ('Module-level expressions must be constants.', 'Move executable expressions inside a function.'),
    'IMPORT_MODULE': ('Only allowlisted modules may be imported, using absolute imports.', 'Use an allowed module or ordinary Python without that import.'),
    'IMPORT_NAME': ('Imported names may not begin with an underscore.', 'Use a public name from an allowed module.'),
    'FORBIDDEN_NAME': ('Dynamic execution, reflection, external access and dunder names are forbidden.', 'Use direct computation on the public input.'),
    'PRIVATE_ATTRIBUTE': ('Private attributes are forbidden.', 'Use public input fields or supported public operations.'),
    'UNSUPPORTED_CAPABILITY': ('Classes, async functions, global and nonlocal declarations are forbidden.', 'Use ordinary functions and local variables.'),
    'DEFINITION_EXECUTION': ('Function definitions cannot execute decorators, annotations or default expressions.', 'Use plain definitions with explicit parameters.'),
    'RETURN': ('The math entry point must explicitly return a permitted result dictionary.', 'Use the frozen status and result fields.'),
    'RETURN_PATH': ('All paths through the math entry point must return.', 'Return an explicit result on every path.'),
}


def _node_sha256(node):
    """Hash AST structure with bounded call depth, omitting all locations."""
    digest = hashlib.sha256()
    pending = [node]
    while pending:
        part = pending.pop()
        if isinstance(part, ast.AST):
            fields = list(ast.iter_fields(part))
            token = ['node', type(part).__name__, [name for name, _ in fields]]
            pending.extend(value for _,value in reversed(fields))
        elif isinstance(part, list):
            token = ['list', len(part)]
            pending.extend(reversed(part))
        else:
            token = ['value', type(part).__name__, repr(part)]
        digest.update(canonical(token).encode()+b'\n')
    return digest.hexdigest()


class SourceDiagnostics:
    """Record legacy error codes and, when requested, the nodes behind them."""

    def __init__(self, source, detailed):
        self.errors = set()
        self.details = [] if detailed else None
        self.lines = source.split('\n') if detailed and isinstance(source, str) else []

    def reject(self, code, node=None, *, rule_id=None, identity=None, syntax_error=None):
        self.errors.add(code)
        if self.details is None:
            return
        rule_id = rule_id or code
        rule, alternative = STATIC_RULES[rule_id]
        line = getattr(node, 'lineno', None)
        offset = getattr(node, 'col_offset', None)
        if syntax_error is not None:
            line = syntax_error.lineno
            if line and line <= len(self.lines) and syntax_error.offset:
                offset = len(self.lines[line-1][:syntax_error.offset-1].encode())
        column = offset+1 if offset is not None else None
        excerpt = ''
        if line and line <= len(self.lines):
            raw = self.lines[line-1].rstrip('\r').encode()
            start = max(0, (offset or 0)-48)
            excerpt = raw[start:start+192].decode(errors='ignore')
        structure = identity if identity is not None else node
        if structure is not None:
            node_hash = _node_sha256(structure)
        else:
            node_hash = fingerprint(syntax_error.msg if syntax_error is not None else rule_id)
        self.details.append(dict(code=code, rule_id=rule_id, line=line, column=column,
            node_type=type(node).__name__ if node is not None else None,
            source_excerpt=excerpt, rule=rule, alternative=alternative,
            node_sha256=node_hash))

    def result(self, checks, **metadata):
        result = dict(passed=not self.errors, errors=sorted(self.errors), **metadata)
        if self.details is not None:
            result.update(diagnostics=sorted(self.details, key=lambda row: (
                row['line'] or 0, row['column'] or 0, row['rule_id'], row['node_sha256'])), checks=checks)
        return result


def validate_math_source(code, *, detailed=False):
    review = SourceDiagnostics(code, detailed)
    checks = dict(source='NOT_CHECKED', parse='NOT_CHECKED', safety='NOT_CHECKED')
    if not isinstance(code, str) or not 1 <= len(code.encode()) <= 65536:
        review.reject('SOURCE_SIZE')
        return review.result(dict(checks, source='REJECTED'))
    checks['source'] = 'PASSED'
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        review.reject('SYNTAX', syntax_error=error)
        return review.result(dict(checks, parse='REJECTED'))
    checks['parse'] = 'PASSED'
    if len(list(ast.walk(tree)))>12000:
        review.reject('AST_SIZE')
    entries = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='math_operator']
    if len(entries)!=1:
        for entry in entries or [None]:
            review.reject('ENTRY', entry, rule_id='MATH_ENTRY')
    else:
        entry = entries[0]
        a = entry.args
        if (len(a.args)+len(a.posonlyargs)!=1 or a.vararg or a.kwarg or a.kwonlyargs or a.defaults
                or entry.decorator_list or entry.returns or any(x.annotation for x in a.args+a.posonlyargs)):
            review.reject('SIGNATURE', entry, rule_id='MATH_SIGNATURE', identity=a)
    for node in tree.body:
        if not isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign,ast.Expr)):
            review.reject('TOP_LEVEL', node)
        if isinstance(node,ast.Expr) and not isinstance(node.value,ast.Constant):
            review.reject('TOP_LEVEL_EXECUTION', node.value, rule_id='MODULE_EXPRESSION_CONSTANT')
        if isinstance(node,ast.Assign):
            try:
                ast.literal_eval(node.value)
            except (ValueError,TypeError):
                review.reject('TOP_LEVEL_EXECUTION', node.value, rule_id='MODULE_ASSIGNMENT_LITERAL', identity=node)
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORTS:
                    review.reject('IMPORT', alias, rule_id='IMPORT_MODULE')
        if isinstance(node,ast.ImportFrom):
            if node.level or node.module not in ALLOWED_IMPORTS:
                review.reject('IMPORT', node, rule_id='IMPORT_MODULE')
            for alias in node.names:
                if alias.name.startswith('_'):
                    review.reject('IMPORT', alias, rule_id='IMPORT_NAME')
        if isinstance(node,ast.Name) and (node.id in FORBIDDEN or node.id.startswith('__')):
            review.reject('FORBIDDEN_NAME', node)
        if isinstance(node,ast.Attribute) and node.attr.startswith('_'):
            review.reject('PRIVATE_ATTRIBUTE', node)
        if isinstance(node,(ast.AsyncFunctionDef,ast.ClassDef,ast.Global,ast.Nonlocal)):
            review.reject('UNSUPPORTED_CAPABILITY', node)
        if isinstance(node,ast.FunctionDef):
            definition = [*node.decorator_list, *node.args.defaults,
                          *[v for v in node.args.kw_defaults if v is not None]]
            definition += [a.annotation for a in node.args.args+node.args.posonlyargs+node.args.kwonlyargs
                           if a.annotation is not None]
            if node.returns is not None:
                definition.append(node.returns)
            for part in definition:
                review.reject('DEFINITION_EXECUTION', part)
    if entries:
        returns = []

        def visit(node):
            if isinstance(node,(ast.FunctionDef,ast.Lambda)):
                return
            if isinstance(node,ast.Return):
                returns.append(node)
            for child in ast.iter_child_nodes(node):
                visit(child)

        for node in entries[0].body:
            visit(node)
        for returned in returns:
            value = returned.value
            if not isinstance(value,ast.Dict) or any(not isinstance(k,ast.Constant) or not isinstance(k.value,str) for k in value.keys):
                review.reject('RETURN', returned)
                continue
            pairs = {k.value:v for k,v in zip(value.keys,value.values)}
            status = pairs.get('status')
            status = status.value if isinstance(status,ast.Constant) else None
            want = {'status','answer'} if status=='APPLIED' else {'status','reason'}
            if status not in ('APPLIED','DECLINED','ERROR') or set(pairs)!=want:
                review.reject('RETURN', returned)
        if not returns or exit_paths(entries[0].body)&{'NEXT','BREAK','CONTINUE','UNVERIFIED'}:
            review.reject('RETURN_PATH', entries[0])
    checks['safety'] = 'REJECTED' if review.errors else 'PASSED'
    return review.result(checks, source_sha256=hashlib.sha256(code.encode()).hexdigest(), protocol=VERSION,
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
        if "operator_contract" in artifact:
            from .operator_contract import binding
            binding(artifact)
        self.events.append('MATH_SHADOW',artifact,time.time())
    def admit(self,artifact,validation,*,after_sequence):
        from .operator_contract import require_release
        require_release(self,artifact)
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
            if 'operator_contract' in a:
                from .operator_contract import require_release
                try:require_release(self,a)
                except (PermissionError,ValueError,OSError):continue
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
