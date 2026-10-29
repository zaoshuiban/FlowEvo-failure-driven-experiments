"""New host-authored semantic benchmark, not a reproduction or natural-problem benchmark.
Reference answers use an existing frozen private oracle, never the candidate algorithm.
"""
import json,sys,ast,time,random,hashlib,re
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
from run_math_v3_development import ROOT,DATA,save,sha
from failure_evo.contracts import fingerprint
OLD=ROOT/'runs/math_v31_semantic_20261027_01'
REF=DATA/'private/original_sources/scripts/baseline_failure_mechanisms_v2.py'
# Each positive specifies exact fixed-order binary-tree semantics. No operator code is generated here.
DEV=[
 'For {e}, place parentheses in all possible ways, keeping both the numbers and operations in their written order. Count the distinct numerical answers, merging equal answers.',
 'Consider {e}. Rearranging is not allowed. By inserting parentheses, how many distinct values can be obtained?',
 'Take the ordered operand list {nums} and intervening operation list {ops}. Every full binary grouping is permitted; neither list can be permuted. What is the cardinality of the set of resulting integer values?',
 'Expression: {e}. Evaluate every full parenthesization that preserves its token order. Report the size of the set of outputs, not the number of syntax trees.',
 'Use {e} exactly as printed. The only freedom is the grouping of its binary operations. Equal numerical outcomes are merged. How many outcomes remain?',
 'In {e}, do not change or reorder the integer operands or binary signs. Add parentheses in every possible manner. How many different numerical results occur?',
 'For the chain {e}, count attainable integer values over all order-preserving binary groupings. Two groupings with equal values contribute one value.',
 'Insert parentheses into {e} without moving or replacing any token. Count numerical results only once when multiple placements give the same number.',
 'A fixed-order calculation is written {e}. How large is the set of answers from all binary parenthesizations? Count answers, rather than parenthesization forms.',
 'One expression consists solely of the integer {single}. There are no operations to insert or reorder. What is the number of distinct results of its full binary parenthesizations?',
 'The integers in {e} and the printed operations must remain in order. Group the operations arbitrarily with parentheses. Determine the number of unique values.',
 'Consider the fixed chain {e}. Obtain the integer for every legal full binary grouping. Remove duplicate integers and report how many remain.'
]
GATE=[
 'What is the cardinality of V for the formula {e}? V contains the evaluated outcomes of every full binary bracketing of the printed operands and signs; order is preserved and duplicate outcomes are identified.',
 'The leaves of a binary arithmetic tree, from left to right, must be {nums}. The in-order binary labels must be {ops}. Count different integer evaluations across all such trees; identical evaluations are counted once.',
 'Read {e} as an ordered sequence of literals and binary operations, with no precedence imposed. Range over every grouping into binary applications, retaining order. How many integers can appear?',
 'For the immutable arithmetic string {e}, enumerate bracket placements conceptually and then identify placements with equal output. Give the number of equivalence classes under equality of numerical output.',
 'How many members does the numerical result set have for {e} when only association of binary operations may vary and operand and operator order cannot vary?',
 'Keep the written token sequence {e}. Each possible binary parse has an integer value. Return the number of different values of these parses, counting duplicates once.',
 'Start with {e}. No numeral or sign may be deleted, inserted, or moved; grouping parentheses alone may vary. Determine the count of distinct evaluated integers.',
 'Treat {e} as a chain whose association is unspecified. Preserve the left-to-right operands and operations. Count unique final values across all associations.',
 'All ways of bracketing the ordered expression {e} are admitted. Collapse equal numerical answers into a single element. What is the resulting set size?',
 'A tree has exactly one leaf labelled {single} and no internal vertices. What is the size of the set of values of all full binary arithmetic trees satisfying this description?',
 'For {e}, any binary association is legal, but every original operand and sign stays in its position. Count the integer answers without multiplicity.',
 'The ordered lists of operands {nums} and operations {ops} specify a chain. Consider each possible binary tree respecting these lists. Count its possible numerical outputs as a set.'
]
NEG_DEV=[
 'Fully parenthesize {e}, preserving order. What is the largest attainable value?',
 'Fully parenthesize {e}, preserving order. Count every parenthesization separately, even if several give equal results.',
 'Fully parenthesize 11 / 2 + 7, preserving order, and count distinct rational results.',
 'Fully parenthesize 1.5 + 2 * 7, preserving order, and count distinct numerical results.',
 'Arrange the numbers in {e} in any order, then add parentheses. Count all distinct results.',
 'Evaluate {e} using standard arithmetic precedence and give that numerical value.',
 'For {e}, fully parenthesize without reordering and return the list of all possible values rather than its size.',
 'Insert parentheses into 2 ^ 3 + 4, preserving order; how many distinct values can be obtained?'
]
NEG_GATE=[
 'Find the minimum numerical evaluation among order-preserving binary groupings of {e}.',
 'How many binary parse trees respect the token sequence {e}? Numerical equality does not merge trees.',
 'Count distinct outputs of order-preserving bracketings of 13 ÷ 2 - 3.',
 'Count attainable exact results of binary regroupings of 0.75 * 8 - 2 without changing order.',
 'Compute the number of distinct answers using all permutations of operands of {e} and all binary groupings.',
 'What integer does {e} denote under the usual precedence rules? No alternative grouping is requested.',
 'Supply the sum of all distinct results of fully bracketing {e} without rearranging its symbols.',
 'Use the chain 3 ** 2 - 5 with exponentiation and subtraction. Count the distinct values of all order-preserving groupings.'
]
AMB_DEV=[
 'For {e}, retain the original operand order, but you are also free to permute all operands. Count the distinct results over permitted parenthesizations.',
 'A chain has operands {nums}; its operations have not been specified. How many values can its binary groupings produce?',
 'Regroup {e} in unspecified ways. Report the required quantity; no quantity has been specified.',
 'For {e}, count numerical results once each and also count equal results separately. Give the total.'
]
AMB_GATE=[
 'All symbols of {e} must retain their positions. Any permutation of those same symbols is allowed. Count numerical outputs over the legal bracketings.',
 'The fixed operands are {nums}. The operator between each adjacent pair is unknown. Determine the size of the set of evaluations.',
 'Consider binary associations of {e}. The requested numerical statistic is missing from the question.',
 'For bracketings of {e}, identify equal output values and do not identify equal output values. How many counted items result?'
]
def prepare(out):
 if out.exists():raise RuntimeError('new pool only')
 original=load(OLD/'inputs.json');a=load(OLD/'F3_F/artifact.json');scores=load(OLD/'development/scores.json');oldcases=load(OLD/'development/cases.json');by={(c['algorithm'],c['task']['task_id']):c for c in oldcases}
 # Historical evidence is fixed before new cases are created. No matcher source supplied to F.
 chosen=[]
 for r in scores:
  use=(r['algorithm']=='F3' and r['condition']=='F' and r['role']=='GeneratedDevelopment' and r['supported'] is True and not r['correct_accept']) or (r['algorithm']=='T3' and r['condition']=='T' and r['role']=='Design' and r['false_accept']) or (r['algorithm']=='T3' and r['condition']=='F' and r['role']=='GeneratedDevelopment' and r['ambiguous_accept'])
  if use:
   c=by[r['algorithm'],r['task_id']];chosen.append(dict(task=c['task'],supported_by_prior_review=r['supported'],observed_match=r['observation']['match'],observed_status=r['observation']['status'],reason='OVER_REFUSAL' if r['supported'] is True else 'FALSE_ACCEPT' if r['supported'] is False else 'UNRESOLVED_SEMANTICS_ACCEPTED',source_record_sha256=fingerprint(r),source_run=OLD.name,source_lock=load(OLD/'development/lock.json')))
 assert len(chosen)==8
 save(out/'historical_evidence.json',chosen)
 source_questions=original['F3_T']['source_problems'];save(out/'shared_generation_input.json',dict(solver_code=Path(a['solver_path']).read_text(),solver_sha256=a['solver_sha256'],parameter_schema=json.loads(a['contract']['parameter_schema']),source_problems=source_questions))
 # Private oracle: reuse the pre-existing exact reference recursion only.
 tree=ast.parse(REF.read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_parenthesized_values');ns=dict(Fraction=Fraction,lru_cache=lru_cache);exec(compile(ast.Module(body=[f],type_ignores=[]),str(REF),'exec'),ns)
 forbidden={fingerprint(c['task']['problem']) for c in oldcases};prior_params={fingerprint(c['parameters']) for c in oldcases if c['parameters']};used=set();public={};private={}
 for role,pos,neg,amb,seed in [('Development',DEV,NEG_DEV,AMB_DEV,326102801),('Gate',GATE,NEG_GATE,AMB_GATE,326102802)]:
  rng=random.Random(seed);pub=[];priv=[]
  for i,(label,template) in enumerate([(True,t) for t in pos]+[(False,t) for t in neg]+[(None,t) for t in amb]):
   nums=[rng.randint(11,39) for _ in range(4+i%3)];ops=[rng.choice(['+','-','*']) for _ in nums[1:]]
   if i==9:nums=[rng.randint(41,99)];ops=[]
   params=dict(operands=nums,operators=ops);ph=fingerprint(params);assert ph not in used and ph not in prior_params;used.add(ph)
   expr=' '.join(str(v) for pair in zip(nums,ops+['']) for v in pair if v!='');q=template.format(e=expr,nums=', '.join(map(str,nums)),ops=', '.join(ops),single=nums[0]);h=fingerprint(q);assert h not in forbidden;forbidden.add(h)
   tid='v32-'+role.lower()+'-'+str(i).zfill(2);pub.append(dict(task_id=tid,problem=q));priv.append(dict(task_id=tid,supported=label,parameters=params if label is True else None,answer=str(len(ns['_parenthesized_values'](tuple(nums),tuple(ops)))) if label is True else None,problem_sha256=h,lineage=dict(origin='V32_HOST_AUTHORED_NEW_CASE',parameter_sha256=ph if label is True else fingerprint(re.findall(r'\d+|[+*/^÷.-]',q)),template_sha256=fingerprint(template),role=role),review='Explicit preservation of operand/operator order and count of distinct integer outputs' if label is True else 'Explicit incompatible quantity, operation domain, or permission to reorder' if label is False else 'Contradictory permissions or missing operations/quantity; no forced label'))
  save(out/'public'/f'{role.lower()}.json',pub);save(out/'private'/f'{role.lower()}.json',priv);public[role]=pub;private[role]=priv
 assert not {r['lineage']['parameter_sha256'] for r in private['Development']}&{r['lineage']['parameter_sha256'] for r in private['Gate']}
 save(out/'manifest.json',dict(created_at=time.time(),roles={r:dict(total=len(public[r]),supported=12,unsupported=8,ambiguous=4) for r in public},history_evidence_count=len(chosen),shared_algorithm_sha256=a['solver_sha256'],old_artifact=a,reference_sha256=sha(REF),reference_path=str(REF),script_sha256=sha(__file__),files={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},lineage_claim='new host-authored synthetic parameters and disjoint phrasing templates, no shared canonical arithmetic parameter sequence; same mathematical family, NOT different natural original problems',gate_policy='All frozen valid candidates may undergo one isolated confirmatory evaluation, regardless of development result; no revision or deployment; development failures stay Shadow. Research evaluation is not Experimental admission.',history_timestamp_boundary='V3.1 locked before pool creation; Gate never supplied to any generation request'))
 print(out,flush=True)
def load(p):return json.loads(p.read_text())
if __name__=='__main__':prepare(Path(sys.argv[1]).resolve())
