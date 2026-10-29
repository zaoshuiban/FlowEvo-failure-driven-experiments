"""New author specifications, fixed before model calls; no operator implementation."""
import ast,random
from fractions import Fraction
from functools import lru_cache
from run_math_v3_development import DATA,save,sha
from failure_evo.contracts import fingerprint
DEV=[
 'For the sequence {e}, keep every literal and operator in its position. All full binary associations are legal. Count the distinct numerical values produced.',
 'Use leaves {nums}, in exactly that order, and intervening operators {ops}, in exactly that order. Consider all full binary trees with these leaves and operators. How many different evaluated numbers occur?',
 'There is one literal, {n}, and no operators. Across all binary expression trees with exactly this leaf and no other nodes, report the number of distinct evaluations.',
 'Read {e} as a fixed sequence, including the sign of a negative literal. No conventional precedence is imposed; any full binary grouping is allowed. Count numerical outcomes, merging duplicates.',
 'For {e}, only parentheses may change. All original tokens must remain in order. Every binary bracketing is possible. Find the cardinality of the evaluated-value set.',
 'Association is the only freedom in {e}; no reordering or token replacement is allowed. Take every full binary association and report how many unique results it yields.'
]
CONF=[
 'A machine receives {e} as an immutable token tape. Its execution tree may be any full binary tree preserving the tape. Outputs of equal value are identified. How many output classes are possible?',
 'The ordered leaves are {nums}; the in-order operation labels are {ops}. Neither ordered list may vary. What is the number of distinct integer evaluations across all full binary tree shapes?',
 'A calculation has a single terminal labelled {n}, no other terminals, and no operation nodes. Among all full binary calculations meeting this description, how large is the numerical output set?',
 'Given {e}, retain each literal (including its sign) and binary operation in order. Let association range over all choices. Enumerate distinct final numbers conceptually and give their count.',
 'For {e}, discard precedence but do not permute or replace symbols. Allow every full binary parse. The requested result is the size of the set of numerical parse evaluations.',
 'No changes to the token tape {e} are permitted except selecting its binary association. Any such association is allowed. Report the number of unequal evaluated outcomes.'
]
NEGDEV=[
 ('Sum the distinct numerical evaluations of all fixed-order full binary groupings of {e}. Give the sum, not the number of evaluations.','goal'),
 ('Keep 67 / 4 + 19 - 8 in its printed order. Count distinct exact results across all full binary associations.','division'),
 ('For {e}, freely permute the operands while keeping the signs in order, and use all full binary groupings. Count distinct numerical results.','reorder'),
 ('Treat 1.25 * 16 - 7 + 3 as exact decimal arithmetic. Preserve the token order and count distinct outputs over all full binary groupings.','decimal')]
NEGCONF=[
 ('For all full binary groupings of the immutable sequence {e}, report the smallest numerical evaluation.','goal'),
 ('Evaluate all fixed-order full binary associations of 5 ** 3 - 17 + 6, where ** denotes exponentiation. Count their distinct results.','exponent'),
 ('Parenthesize {e} in all possible ways without moving tokens. Count binary tree structures separately even if their evaluations agree.','trees'),
 ('The parentheses in (73 - 21) * (14 + 5) are mandatory and cannot change. Count numerical results consistent with exactly these fixed groups.','fixed')]
AMBDEV=[
 'For {e}, count distinct values from full binary groupings. Whether operands or operators may be reordered is not specified.',
 'The operands {nums} must retain order, but the intervening binary operations are not specified. How many distinct results can all binary groupings give?']
AMBCONF=[
 'For {e}, full binary associations may be chosen. The question does not specify whether rearranging its tokens is permitted. Count the different numerical evaluations.',
 'For the fixed-order tape {e}, all full binary associations are allowed. Count equal results only once and also count equal results separately for each tree. Give a single count.']
def prepare(out):
 ref=DATA/'private/original_sources/scripts/baseline_failure_mechanisms_v2.py';f=next(n for n in ast.parse(ref.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_parenthesized_values');ns=dict(Fraction=Fraction,lru_cache=lru_cache);exec(compile(ast.Module(body=[f],type_ignores=[]),str(ref),'exec'),ns)
 allparams=set()
 for role,pos,neg,amb,seed in [('development',DEV,NEGDEV,AMBDEV,3400281),('confirmation',CONF,NEGCONF,AMBCONF,3400282)]:
  rng=random.Random(seed);pub=[];private=[]
  specs=[(True,'supported',x) for x in pos]+[(False,k,x) for x,k in neg]+[(None,'missing' if i==0 or role=='development' else 'contradictory',x) for i,x in enumerate(amb)]
  for i,(label,category,template) in enumerate(specs):
   nums=[rng.randint(54,98),rng.randint(14,29),rng.randint(4,13),rng.randint(2,9)];ops=[rng.choice(['+','-','*']) for _ in range(3)]
   if i==2:nums=[rng.randint(110,199)];ops=[]
   if i==3:nums[0]=-nums[0]
   e=' '.join(str(v) for pair in zip(nums,ops+['']) for v in pair if v!='');q=template.format(e=e,nums=', '.join(map(str,nums)),ops=', '.join(ops),n=nums[0]);tid=f'v34-{role}-{i:02}';params=dict(operands=nums,operators=ops)
   if label is True:assert fingerprint(params) not in allparams;allparams.add(fingerprint(params))
   pub.append(dict(task_id=tid,problem=q));private.append(dict(task_id=tid,problem_sha256=fingerprint(q),supported=label,category=category,parameters=params if label is True else None,answer=str(len(ns['_parenthesized_values'](tuple(nums),tuple(ops)))) if label is True else None,template_sha256=fingerprint(template),review='Host-authored and host-reviewed explicit semantics, not third-party blind review; numeric oracle is independent existing Fraction reference.'))
  save(out/f'data/public/{role}.json',pub);save(out/f'data/private/{role}.json',private)
 save(out/'data/reference.json',dict(source=str(ref),sha256=sha(ref),oracle_not_candidate=True,synthetic_same_family=True))
