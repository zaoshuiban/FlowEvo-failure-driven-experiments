"""Bounded source inspection, never execution or proof of functional correctness."""
import ast

VERSION = 'operator-static-contract-v2'


def exit_paths(body):
    """Overapproximate explicit control transfers; NEXT means possible fall-through.

    Exceptions from expressions remain a runtime concern. Loops are never assumed
    to run or terminate. Unsupported compound syntax is explicitly unverified.
    """
    paths = {'NEXT'}
    for node in body:
        if 'NEXT' not in paths:
            break
        paths = (paths - {'NEXT'}) | statement_paths(node)
    return paths


def statement_paths(node):
    if isinstance(node, ast.Return):
        return {'RETURN'}
    if isinstance(node, ast.Raise):
        return {'RAISE'}
    if isinstance(node, ast.Break):
        return {'BREAK'}
    if isinstance(node, ast.Continue):
        return {'CONTINUE'}
    if isinstance(node, ast.If):
        return exit_paths(node.body) | exit_paths(node.orelse)
    if isinstance(node, ast.Try):
        body = exit_paths(node.body)
        paths = body - {'NEXT'}
        if 'NEXT' in body:
            paths |= exit_paths(node.orelse)
        # Every handler is conservatively reachable, including from expressions.
        for handler in node.handlers:
            paths |= exit_paths(handler.body)
        if node.finalbody:
            final = exit_paths(node.finalbody)
            paths = (paths if 'NEXT' in final else set()) | (final - {'NEXT'})
        return paths
    if isinstance(node, (ast.For, ast.While)):
        body = exit_paths(node.body)
        paths = (body - {'NEXT', 'BREAK', 'CONTINUE'}) | exit_paths(node.orelse)
        if 'BREAK' in body:
            paths.add('NEXT')
        # Without else, an empty iteration already contributes NEXT.
        return paths
    if isinstance(node, (ast.With, ast.AsyncWith, ast.AsyncFor)) or type(node).__name__ in ('Match', 'TryStar'):
        return {'UNVERIFIED', 'NEXT'}
    return {'NEXT'}


def public_case_field_findings(entry):
    """Recognize simple aliases from context to projected public cases.

    This is a limited lint, not whole-program dataflow. Unknown/reassigned aliases
    are not asserted to be host fields; coverage is reported by the caller.
    """
    nodes = []
    def collect(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return
        nodes.append(node)
        for child in ast.iter_child_nodes(node):
            collect(child)
    for node in entry.body:
        collect(node)
    params = entry.args.posonlyargs + entry.args.args
    if len(params) != 1:
        return []
    definitions = {}
    for node in nodes:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    definitions.setdefault(target.id, []).append(('value', node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            definitions.setdefault(node.target.id, []).append(('value', node.value))
        elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            definitions.setdefault(node.target.id, []).append(('item', node.iter))
    roles = {params[0].arg: 'context'}
    transitions = {('context','candidate_ledger'):'ledger',
                   ('context','public_feedback'):'feedback',
                   ('row','public_feedback'):'feedback',
                   ('feedback','public_cases'):'cases'}
    def access(node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and node.args:
            return node.func.value, node.args[0]
        if isinstance(node, ast.Subscript):
            return node.value, node.slice
        return None, None
    def role(node):
        if isinstance(node, ast.Name):
            return roles.get(node.id)
        base, key = access(node)
        if base is not None and isinstance(key, ast.Constant):
            base_role = role(base)
            if base_role == 'cases' and isinstance(key.value, int):
                return 'case'
            if base_role == 'ledger' and isinstance(key.value, int):
                return 'row'
            return transitions.get((base_role, key.value))
        return None
    for _ in range(len(definitions) + 1):
        updated = dict(roles)
        for name, defs in definitions.items():
            if len(defs) != 1:
                updated.pop(name, None)
                continue
            kind, value = defs[0]
            inferred = role(value)
            if kind == 'item':
                inferred = {'ledger':'row', 'cases':'case'}.get(inferred)
            if inferred:
                updated[name] = inferred
        if updated == roles:
            break
        roles = updated
    findings = []
    allowed = {'input', 'expected', 'actual', 'exception_class'}
    for node in nodes:
        base, key = access(node)
        if base is not None and role(base) == 'case' and isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value not in allowed:
            findings.append(dict(code='COMPILE_CONTEXT_CONTRACT_ERROR',line=node.lineno,
                                 field='public_feedback.public_cases[].'+key.value,
                                 reason='Field is absent from PublicFeedback.project output'))
    return findings
