import pathlib,json,collections,datetime
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1]
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
F=R/'runs/s20_taco80_f_20261025_01';M=R/'runs/s20_taco80_m_20261025_01'
out={}
for arm,p in [('M',M),('F',F)]:
 packets=[read(x) for x in p.glob('public_packets/*.json')];out[arm]=dict(failure_events=len(packets),independent_tasks=len({x['task_id'] for x in packets}))
m=read(M/'state.json');out['M'].update(memory=m['memory'],attempts=list(m['outputs'].values()),reason='boundary sends ALL accumulated full packets to update_memory; no LearningEvidenceBundle compression in M path')
n=[]
for p in F.glob('jobs/*/*-normalization.json'):
 d=read(p);n.append(dict(path=str(p.relative_to(R)),accepted=d['accepted'],error=d.get('error'),slot=int(p.name.split('-')[0])))
out['F'].update(normalizations=n,error_counts=dict(collections.Counter(x['error'] for x in n if not x['accepted'])),slots=dict(collections.Counter(x['slot'] for x in n)),capabilities=[])
for p in F.glob('jobs/*/*-capability.json'):
 d=read(p);obs=d['observations'];matched=[x for x in obs if x['matched']];out['F']['capabilities'].append(dict(path=str(p.relative_to(R)),rule_duplicate=d['rule_duplicate'],source_effect=d['source_effect'],matched=len(matched),matched_changed_generic=sum(bool(x['changed_generic_action']) for x in matched),request_audit={k:v for k,v in d.items() if 'request' in k}))
out['F']['assessments']=[]
for p in F.glob('assessments/*.json'):
 d=read(p);packet=read(F/'public_packets'/(d['source_event_id']+'.json'));out['F']['assessments'].append(dict(path=str(p.relative_to(R)),source_task=packet['task_id'],level=d['level'],before=d['before']['status'],after=d['after']['status'],tests_passed=d['after']['tests_passed'],tests_run=d['after']['tests_run']))
u=[x for x in rows(F/'solve_budget.jsonl') if x['payload'].get('request_id')=='F/s19g_taco-train-s00-r1204/1'];out['unknown_request']=u;out['lock_reason']='User explicitly authorized skipping one infrastructure-missing task; recovery filters this request from blockers ONLY, preserving UNKNOWN journal and full reservation; virtual cursor skip is not persisted as TASK_FINALIZED. ONLINE_LOCKED locks trajectory, not proof of settled billing or 80 evaluations.'
(P/'mechanism_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({a:{k:v for k,v in out[a].items() if k in ['failure_events','independent_tasks','error_counts','slots','assessments','capabilities']} for a in ['M','F']},ensure_ascii=False))
