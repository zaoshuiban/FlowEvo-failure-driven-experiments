"""Read-only frozen A4 analysis; no environment/model imports."""
import argparse,json,hashlib
from pathlib import Path
from collections import Counter
ARMS=['S0','S1','Rule','A3b_candidate_0']
def read(p):return json.loads(p.read_text())
def summarize(rows):
 d={k:[r for r in rows if r['expected']==k] for k in ['MATCH','DECLINE','UNKNOWN']}
 def n(k,f):return {'numerator':sum(f(r) for r in d[k]),'denominator':len(d[k]),'status':'EVALUABLE' if d[k] else 'NOT_EVALUABLE'}
 result=dict(records=len(rows),games=len({r['game_sha256'] for r in rows}),groups=len({r['physical_state_group_id'] for r in rows}),
  gate_status=dict(Counter(r['decision']['status'] for r in rows)),
  positive_intervention=n('MATCH',lambda r:r['actual_intervention']),repair=n('MATCH',lambda r:r['trusted_positive_repair']),
  negative_gate_match=n('DECLINE',lambda r:r['decision']['status']=='MATCH'),unknown_gate_match=n('UNKNOWN',lambda r:r['decision']['status']=='MATCH'),
  negative_intervention=n('DECLINE',lambda r:r['actual_intervention']),unknown_intervention=n('UNKNOWN',lambda r:r['actual_intervention']),
  bounded_wins=sum(bool(r['live'] and r['live']['won']) for r in rows),errors=sum(r['decision']['status']=='ERROR' or bool(r['live'] and r['live']['stop']=='CANDIDATE_ERROR') for r in rows),
  actions=sum(len(r['live']['actions']) if r['live'] else 0 for r in rows),decision_seconds=sum(r['decision_seconds'] for r in rows))
 if rows and all(r['arm']=='S0' for r in rows):
  for k in ['negative_gate_match','unknown_gate_match']:result[k]={'status':'NOT_APPLICABLE_UNGATED','numerator':None,'denominator':result[k]['denominator']}
 return result
def analyze(root):
 result=read(root/'result.json');rows=result.get('rows',[]);metrics={}
 for stratum in ['strict_scene','expanded_game_group']:
  metrics[stratum]={a:summarize([r for r in rows if r['stratum']==stratum and r['arm']==a]) for a in ARMS}
 paired=[]
 for a in ['S0','S1','Rule']:
  old={r['sample_id']:r for r in rows if r['arm']==a};new={r['sample_id']:r for r in rows if r['arm']=='A3b_candidate_0'}
  assert old.keys()==new.keys()
  for stratum in metrics:
   ids=[k for k in old if old[k]['stratum']==stratum];pos=[k for k in ids if old[k]['expected']=='MATCH'];neg=[k for k in ids if old[k]['expected']!='MATCH']
   paired.append(dict(reference=a,stratum=stratum,independent_games=len({old[k]['game_sha256'] for k in ids}),new_only_repair=sum(new[k]['trusted_positive_repair'] and not old[k]['trusted_positive_repair'] for k in pos),lost_repair=sum(old[k]['trusted_positive_repair'] and not new[k]['trusted_positive_repair'] for k in pos),avoided_nonpositive_intervention=sum(old[k]['actual_intervention'] and not new[k]['actual_intervention'] for k in neg),new_nonpositive_intervention=sum(new[k]['actual_intervention'] and not old[k]['actual_intervention'] for k in neg)))
 reg=result['regression'];rr=reg['rows'];regsummary={'retained':sum(r.get('repaired',False) for r in rr),'sources':sum(r['role']=='EXPOSED_SOURCE' for r in rr),'boundary':sum(r['role']=='EXPOSED_BOUNDARY' for r in rr),'boundary_decisions':dict(Counter((r['expected']+':'+r['decision']['status']) for r in rr if r['role']=='EXPOSED_BOUNDARY'))}
 data=dict(status=result['status'],metrics=metrics,paired=paired,regression=regsummary,budget=result['budget'],result_sha256=hashlib.sha256((root/'result.json').read_bytes()).hexdigest(),inference='descriptive clustered checkpoints; no significance claim; no online episode uplift claim')
 out=root/'analysis.json';s=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
 if out.exists():assert out.read_text()==s
 else:out.write_text(s)
 return data
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();print(json.dumps(analyze(a.run),ensure_ascii=False))
