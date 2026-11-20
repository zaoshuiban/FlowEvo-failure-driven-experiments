"""TACO's bounded JSON function subset. Public examples originate in the statement.

No solutions or private cases belong to a public task. Method adaptation changes
only the invocation interface and never implements a task algorithm.
"""
import ast
import copy
import json
import re
from pathlib import Path
from core.schemas import CodeTaskInstance
from failure_evo.skill_runtime import sha


def signature(starter, entry):
    # Dataset starters usually have an unfinished, indented body.
    tree = ast.parse(starter.rstrip() + '\n        pass\n')
    cls = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    if cls:
        if len(cls)!=1 or cls[0].name!='Solution' or cls[0].bases:
            raise ValueError('UNSUPPORTED_CLASS')
        methods=[n for n in cls[0].body if isinstance(n, ast.FunctionDef)]
        if len(methods)!=1 or methods[0].name!=entry:
            raise ValueError('UNSUPPORTED_MULTI_METHOD')
        fn=methods[0]; kind='solution_method'
    else:
        fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==entry]
        if len(fns)!=1:raise ValueError('ENTRY_SIGNATURE_MISSING')
        fn=fns[0];kind='function'
    args=list(fn.args.args)
    if kind=='solution_method':
        if not args or args[0].arg!='self':raise ValueError('UNSUPPORTED_METHOD_BINDING')
        args=args[1:]
    if fn.args.vararg or fn.args.kwarg or fn.args.posonlyargs or fn.args.kwonlyargs:
        raise ValueError('UNSUPPORTED_VARIADIC_SIGNATURE')
    annotations=[ast.unparse(a.annotation) if a.annotation else '' for a in args]
    if any(re.search(r'TreeNode|ListNode|Node|Iterator|Callable',a) for a in annotations):
        raise ValueError('UNSUPPORTED_CUSTOM_TYPE')
    return dict(kind=kind,entry_point=entry,parameters=[a.arg for a in args],
                annotations=annotations,required=len(args)-len(fn.args.defaults),
                returns=ast.unparse(fn.returns) if fn.returns else '')


def literal(s):
    s=s.strip().strip('`').strip()
    # JSON literals only; never evaluate calls, expressions or arbitrary setup.
    try:return json.loads(s)
    except (ValueError,TypeError):return ast.literal_eval(s)


def json_value(value):
    if value is None or type(value) in (int,bool,str):return True
    if isinstance(value,(list,tuple)):return all(json_value(x) for x in value)
    if isinstance(value,dict):return all(isinstance(k,str) and json_value(v) for k,v in value.items())
    return False  # floats, sets, object construction need a reviewed comparator


def call_case(expr, expected, spec, evidence):
    node=ast.parse(expr.strip(),mode='eval').body
    if not isinstance(node,ast.Call):raise ValueError('NOT_CALL')
    name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
    if name!=spec['entry_point']:raise ValueError('WRONG_ENTRY')
    args=[ast.literal_eval(n) for n in node.args]
    kwargs={n.arg:ast.literal_eval(n.value) for n in node.keywords if n.arg is not None}
    if len(kwargs)!=len(node.keywords):raise ValueError('EXPANDED_KWARGS')
    if not spec['required']<=len(args)+len(kwargs)<=len(spec['parameters']):raise ValueError('ARITY')
    if any(k not in spec['parameters'][len(args):] for k in kwargs):raise ValueError('KEYWORD')
    value=literal(expected)
    if not all(json_value(v) for v in [args,kwargs,value]):raise ValueError('NON_JSON_OR_FLOAT')
    return dict(args=args,kwargs=kwargs,expected=value,public_evidence=evidence)


def public_examples(question,spec):
    """Conservative literal syntax only. Unsupported examples are not invented."""
    entry=spec['entry_point'];cases=[]
    def add(expr,out,evidence):
        try:cases.append(call_case(expr,out,spec,evidence))
        except (SyntaxError,ValueError,TypeError):pass
    for line in question.splitlines():
        line=line.strip().strip('`').strip()
        # Codewars assert_equals(function(...), expected) is entirely public.
        try:
            node=ast.parse(line,mode='eval').body
            if isinstance(node,ast.Call) and len(node.args)>=2 and isinstance(node.args[0],ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else getattr(node.func,'id','')
                if name in {'assert_equals','assertEqual'}:
                    add(ast.unparse(node.args[0]),ast.unparse(node.args[1]),line)
        except SyntaxError:pass
        m=re.match(r'(.*?\))\s*(?:#\s*)?(?:=>|==|->|-->)\s*(.+?)\s*$',line)
        if m:add(m[1],m[2].split(' #')[0],line)
        # A single-argument public mapping: literal -> literal.
        if len(spec['parameters'])==1:
            m=re.match(r'(.+?)\s*(?:->|=>)\s*(.+)',line)
            if m:
                try:add(entry+'('+repr(literal(m[1]))+')',m[2],line)
                except (ValueError,SyntaxError):pass
    # LeetCode literal Input/Output blocks (named and positional arguments).
    pat=r'Input:\s*(.*?)\s*Output:\s*([^\n]+)'
    for m in re.finditer(pat,question,re.S|re.I):
        inp=m[1].strip();out=m[2].strip()
        inp=re.sub(r'\btrue\b','True',inp);inp=re.sub(r'\bfalse\b','False',inp);inp=re.sub(r'\bnull\b','None',inp)
        add(entry+'('+inp+')',out,m[0])
    unique={json.dumps([c['args'],c['kwargs'],c['expected']],sort_keys=True):c for c in cases}
    return list(unique.values())


def assertion(entry,case):
    args=', '.join([*(repr(x) for x in case['args']),*(k+'='+repr(v) for k,v in case.get('kwargs',{}).items())])
    return 'assert '+entry+'('+args+') == '+repr(case['expected'])


def invocation_source(source,entry):
    tree=ast.parse(source)
    if any(isinstance(n,ast.FunctionDef) and n.name==entry for n in tree.body):return source
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Solution'),None)
    if cls is None or not any(isinstance(n,ast.FunctionDef) and n.name==entry for n in cls.body):
        raise ValueError('MISSING_TACO_ENTRY')
    # One shared method bridge; preserve the signature/defaults as well as the
    # model's complete class. This introduces no task-specific computation.
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==entry)
    args=copy.deepcopy(method.args)
    if not args.args or args.args[0].arg!='self':raise ValueError('UNSUPPORTED_METHOD_BINDING')
    args.args=args.args[1:]
    positional=[ast.Name(id=a.arg,ctx=ast.Load()) for a in args.posonlyargs+args.args]
    if args.vararg:positional.append(ast.Starred(value=ast.Name(id=args.vararg.arg,ctx=ast.Load()),ctx=ast.Load()))
    keywords=[ast.keyword(arg=a.arg,value=ast.Name(id=a.arg,ctx=ast.Load())) for a in args.kwonlyargs]
    if args.kwarg:keywords.append(ast.keyword(arg=None,value=ast.Name(id=args.kwarg.arg,ctx=ast.Load())))
    body=ast.Return(value=ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id='Solution',ctx=ast.Load()),args=[],keywords=[]),attr=entry,ctx=ast.Load()),args=positional,keywords=keywords))
    bridge=ast.FunctionDef(name=entry,args=args,body=[body],decorator_list=[],returns=copy.deepcopy(method.returns))
    ast.fix_missing_locations(bridge)
    return source.rstrip()+'\n\n'+ast.unparse(bridge)+'\n'


def adapt_candidate(source,entry):
    tree=ast.parse(source)
    end=max((n.end_lineno for n in tree.body if isinstance(n,ast.ImportFrom) and n.module=='__future__'),default=0)
    lines=source.splitlines(keepends=True)
    code=''.join(lines[:end])+'\nfrom typing import List, Dict, Tuple, Optional, Set\n'+''.join(lines[end:])
    return invocation_source(code,entry)


def public_task(row):
    spec=row['call_protocol'];entry=spec['entry_point']
    tests=[assertion(entry,c) for c in row['public_cases']]
    if not tests:raise ValueError('NO_STATEMENT_PUBLIC_CASES')
    fmt='\n\nPython call protocol: '+entry+'('+', '.join(spec['parameters'])+'). Return the result; do not read stdin or print the answer.\n'
    fmt+='A top-level function is accepted. A single Solution method is also accepted via the shared method-call adapter.\nStarter code:\n'+row['starter_code']
    return CodeTaskInstance(task_id=row['problem_id'],benchmark='taco',entry_point=entry,
        prompt=row['public_problem']+fmt,text=row['public_problem'],test_list=tests,visible_public_tests=tests,
        metadata={k:copy.deepcopy(row[k]) for k in ['data_role','source_lineage_id','duplicate_group_id','capability_family_id','call_protocol']} |
          dict(public_validation_only=True,training_validation_public=True,public_training_tests=tests,
               feedback_visibility='public',taco_function_subset=True,starter_code=row['starter_code']))


def scoring_task(row,root):
    path=Path(root)/row['private_scoring_ref']
    if sha(path.read_text())!=row['private_scoring_sha256']:raise ValueError('PRIVATE_SCORER_DRIFT')
    pack=json.loads(path.read_text())
    task=public_task(row)
    task.metadata['public_validation_only']=False
    task.metadata['feedback_visibility']='private'
    task.test_list=[assertion(task.entry_point,c) for c in pack['cases']]
    task.visible_public_tests=[]
    task.metadata.pop('public_training_tests',None)
    return task
