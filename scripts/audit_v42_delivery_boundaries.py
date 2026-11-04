"""Supplementary post-generation regression audit on exposed V4.1 invalid cases."""
import time
import run_v42_delivery_continuation as study
r=study.r;OUT=study.NEW
if __name__=='__main__':
 r.verify()
 if (OUT/'boundary_regression.json').exists():raise RuntimeError('consumed audit')
 cases=[x for x in r.load(r.V4/'private/tests.json') if x['family']=='walk' and x['role']=='unsupported']
 r.save(OUT/'boundary_regression_freeze.json',dict(at=time.time(),cases=cases,source_sha256=r.sha(r.V4/'private/tests.json'),role='POST_HOC_DEVELOPMENT_SAFETY_AUDIT_NOT_NEW_CONFIRMATION',reason='Review shows ordinary revision removed resource guards; execute all ten previously exposed unsupported cases on all versions, no selective deletion'))
 results=[]
 for arm,a in r.load(OUT/'candidate_freeze.json')['versions'].items():
  if a['status']!='STATIC_VALID':continue
  for c in cases:results.append(dict(arm=arm,case_id=c['id'],raw=r.execute(a,c['parameters'])))
 r.save(OUT/'boundary_regression.json',results)
