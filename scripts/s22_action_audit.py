"""Descriptive adherence evidence; never infer algorithm identity or completeness."""
import ast
import difflib
from failure_evo.workflow_protocol_v2 import program_observation

def profile(code):
    result=program_observation(code)
    result.update(characters=len(code),lines=len(code.splitlines()),algorithm_completeness='NOT_ESTABLISHED')
    return result

def compare(before,after,finish_reason=None):
    def nodes(code):
        try:return [type(n).__name__ for n in ast.walk(ast.parse(code))]
        except (SyntaxError,ValueError):return None
    a,b=nodes(before),nodes(after)
    return dict(source=profile(before),output=profile(after),unchanged=before==after,
        character_similarity=difflib.SequenceMatcher(None,before,after,autojunk=False).ratio(),
        ast_node_type_similarity=None if a is None or b is None else difflib.SequenceMatcher(None,a,b,autojunk=False).ratio(),
        finish_reason=finish_reason,truncated=finish_reason=='length',
        algorithm_changed='REQUIRES_MANUAL_REVIEW',
        diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='source',tofile='output')))
