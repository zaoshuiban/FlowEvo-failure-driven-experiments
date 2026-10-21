"""Independent file, dependency and prefix-isolation checks for E3-S0."""
import collections,csv,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    es=lines(R/'events.jsonl');edges=lines(R/'dependency_edges.jsonl');idx={e['event_id']:e for e in es}
    assert len(es)==2132 and len({e['task_id'] for e in es})==800
    assert read(R/'integrity_checks.json')['issue_count']==0
    for name,h in read(R/'source_hashes.json').items():assert sha(R/name)==h,name
    for name,h in read(R/'supporting_evidence_hashes.json').items():assert sha(R.parent/name)==h,name
    for edge in edges:
        a,b=idx[edge['source']],idx[edge['target']]
        assert a['stream']==b['stream'] and a['global_event_index']<b['global_event_index']
        if edge['type']=='PREVIOUS_CODE_AND_OLD_FEEDBACK':
            assert a['task_id']==b['task_id'] and b['stage'] in ['l3','l4'] and not a['old_passed']
        else:assert a['task_id']!=b['task_id'] and a['task_order']<b['task_order'] and a['old_passed']
    rows=list(csv.DictReader((R/'online_accumulation.csv').open()))
    assert len(rows)==len(es)
    # Recompute every prefix using only an allowlist of historically observable fields.
    failures=artifacts=0;tasks=set();artifact_tasks=set();candidate_types=set();prefixes=[]
    for i,e in enumerate(es):
        observed={k:e[k] for k in ['event_id','task_id','old_passed','old_feedback','artifact_syntax','finish_reason']}
        if not observed['old_passed']:
            failures+=1;tasks.add(observed['task_id']);candidate_types.add('observed:'+observed['old_feedback'])
            if observed['artifact_syntax'] in ['EMPTY','SYNTAX_ERROR']:
                artifacts+=1;artifact_tasks.add(observed['task_id']);candidate_types.add('static:'+observed['artifact_syntax'])
            if observed['finish_reason']=='length':candidate_types.add('metadata:output_budget_exhaustion')
        r=rows[i]
        for k,v in {'cumulative_old_failure_events':failures,'cumulative_old_failure_tasks':len(tasks),
          'shadow_static_artifact_failure_events':artifacts,'shadow_static_artifact_failure_tasks':len(artifact_tasks),
          'shadow_observable_candidate_types':len(candidate_types),'historically_certified_functional_failure_tasks':0}.items():assert int(r[k])==v,(i,k)
        if i+1 in [100,500,1000,1500,2132]:
            prefixes.append({'horizon':i+1,'failure_events':failures,'failure_tasks':len(tasks),'artifact_events':artifacts,'observable_candidate_types':len(candidate_types),'historically_certified_functional_tasks':0})
    bank=read(R/'mechanism_candidates.json');roots=[x for x in bank if x['eligible_for_algorithm_failure_memory']]
    assert len(roots)==2 and all(x['event_count']==x['task_count']==1 for x in roots)
    assert all(not e['historical_failure_memory_entries'] for e in es)
    assert len(list(csv.DictReader((R/'candidate_transitions.csv').open())))==2132-800
    result={'status':'PASS','events_checked':2132,'tasks_checked':800,'dependency_edges_checked':len(edges),
      'all_input_hashes_verified':True,'all_2132_prefixes_recomputed_from_observable_allowlist':True,
      'retrospective_labels_excluded_from_shadow_state':True,'snapshot_examples':prefixes,
      'caveat':'Checks establish archival and replay consistency, not semantic correctness of the original evaluator.'}
    (R/'replay_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
