"""Generated tests are proposals, not oracles. Exact approved fixtures only."""
from .contracts import fingerprint
KINDS=('POSITIVE','NEGATIVE','NEAR_MISS','BOUNDARY','AMBIGUOUS')
def parse_proposals(rows):
 if not isinstance(rows,list) or len(rows)>20:raise ValueError('bounded test list')
 for r in rows:
  if not isinstance(r,dict) or set(r)!={'kind','problem','base_problem','changed_dimension','claimed_behavior','invariant'}:raise ValueError('test proposal fields')
  if r['kind'] not in KINDS or any(not isinstance(v,str) for v in r.values()):raise ValueError('test proposal types')
  if not r['problem'].strip() or len(r['problem'])>24000:raise ValueError('test problem')
 return rows
class IndependentOracle:
 """Host supplied sealed reviews, never generated outputs or self-reported truth."""
 def __init__(self,reviewed_rows,*,candidate_hashes):
  self.rows={};self.candidate_hashes=set(candidate_hashes)
  for r in reviewed_rows:
   if r.get('authority')!='HOST_INDEPENDENT_REVIEW' or not r.get('reference_sha256') or r['reference_sha256'] in self.candidate_hashes or r.get('derived_from_candidate') is not False:raise PermissionError('independent oracle provenance required')
   if not r.get('semantic_review_sha256'):raise PermissionError('independent semantic review required')
   key=fingerprint(r['problem'])
   if key in self.rows:raise ValueError('duplicate oracle statement')
   self.rows[key]=r
 def review(self,p):
  r=self.rows.get(fingerprint(p['problem']))
  if r is None:return dict(status='UNVERIFIED',reason='No independent semantic/answer authority for exact generated problem')
  return dict(status='VERIFIED',record=r)
 def audit_all(self,proposals):
  parse_proposals(proposals)
  return [dict(proposal=p,proposal_sha256=fingerprint(p),review=self.review(p)) for p in proposals]
