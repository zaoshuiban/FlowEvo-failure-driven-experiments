"""Separate computation, semantics, combined metrics; all cases are retained."""
from .contracts import fingerprint
from code_math.private_math_scoring import normalized
from code_math.no_gold import PublicMathTask

def compare(answer,expected):
 a,b=normalized(answer),normalized(expected)
 return 'CORRECT' if a==b else 'WRONG' if a[0]==b[0]=='rational' else 'UNVERIFIED'

def evaluate(runner,artifact,cases):
 rows=[]
 for index,case in enumerate(cases):
  review=case['review'];problem=case['proposal']['problem'];task=PublicMathTask('v3-'+fingerprint(problem)[:16],problem)
  # Freeze one output first. Private gold never passed to runner.
  observed=runner.run(artifact,task)
  row=dict(index=index,problem_sha256=fingerprint(problem),observation=observed,computation='UNVERIFIED',applicability='UNVERIFIED',combined='UNVERIFIED',review_status=review['status'])
  if review['status']=='VERIFIED':
   r=review['record'];expected=r.get('supported')
   m=observed['match'];accept=m['status']=='MATCH'
   if expected is False:
    row['applicability']='FALSE_ACCEPT' if accept else 'ERROR' if m['status']=='ERROR' else 'UNKNOWN' if m['status']=='UNKNOWN' else 'CORRECT_REFUSAL'
    row['combined']='CORRECT_REFUSAL' if observed['status']=='DECLINED' else 'ERROR' if observed['status']=='ERROR' else 'FALSE_ACCEPT'
   elif expected is True:
    params=r.get('parameters');params_ok=params is not None and m.get('parameters')==params
    row['applicability']='CORRECT_MATCH' if accept and params_ok else 'PARAMETER_MISMATCH' if accept else m['status']
    # Independent solve uses host-reviewed parameters, never match's own claim.
    if params is not None and r.get('answer') is not None:
     computation=runner.solve(artifact,params)
     row['independent_solve']=computation
     row['computation']=compare(computation['answer'],r['answer']) if computation['status']=='APPLIED' else computation['status']
    if observed['status']=='APPLIED' and params_ok and r.get('answer') is not None:row['combined']=compare(observed['answer'],r['answer'])
    elif observed['status']=='APPLIED':row['combined']='UNVERIFIED' if params is None else 'PARAMETER_MISMATCH'
    else:row['combined']=observed['status']
  rows.append(row)
 return rows

def development_passed(rows):
 supported=[r for r in rows if 'independent_solve' in r]
 negative=[r for r in rows if r['applicability'] in ('CORRECT_REFUSAL','FALSE_ACCEPT','UNKNOWN')]
 return all(r.get('review_status')=='VERIFIED' for r in rows) and bool(supported and negative) and all(r['computation']=='CORRECT' and r['combined']=='CORRECT' for r in supported) and all(r['applicability']=='CORRECT_REFUSAL' for r in negative) and all(r['combined'] not in ('WRONG','FALSE_ACCEPT','ERROR','PARAMETER_MISMATCH') for r in rows)
