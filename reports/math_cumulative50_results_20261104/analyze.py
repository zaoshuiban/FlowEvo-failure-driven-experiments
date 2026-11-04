"""Read-only analysis of the completed cumulative50 run. No model/Worker calls.

Writes only sibling report artifacts. Never normalizes, re-registers, or executes
saved model output. Costs include the copied parent ledger exactly once.
"""
import ast
import collections as C
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
RUN = ROOT / 'runs/math_cumulative50_resume18_20261103_01'
sys.path.insert(0, str(ROOT / 'FlowEvo/src'))
from failure_evo.math_candidate_decision import validate_decision
from failure_evo.persistent_budget import PersistentBudget
from code_math.no_gold import PublicMathTask, solver_messages

def read(p): return json.loads(p.read_text())
def canonical(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def fp(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()] if p.exists() else []
def files(p): return {str(f.relative_to(p)): sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def save(name,v): (OUT/name).write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')
def kinds(p,k): return [r for r in rows(p) if r.get('kind')==k]
def counter(v): return dict(C.Counter(v))
def fields(v, allowed, path):
    if not isinstance(v,dict): return [dict(path=path,error='NOT_OBJECT')]
    extra=sorted(set(v)-set(allowed)); missing=sorted(set(allowed)-set(v))
    return [dict(path=path,extra=extra,missing=missing)] if extra or missing else []

plan=read(RUN/'execution_plan.json'); old_summary=read(RUN/'summary.json')
manifest=read(RUN/'continuation.json'); parent=Path(manifest['parent'])
before={str(p):files(p) for p in [RUN,parent]}
tasks=rows(Path(plan['cumulative_input_bindings']['tasks']['path']))
lineage=read(Path(plan['cumulative_input_bindings']['lineage']['path']))
seq_by_task={t['task_id']:i+1 for i,t in enumerate(tasks)}
errors=[]; chains=0
for p in RUN.rglob('*.jsonl'):
    if 'frozen_source' in p.parts: continue
    rr=rows(p)
    if not rr or 'record_hash' not in rr[0]: continue
    previous='0'*64
    for r in rr:
        if r['previous_hash']!=previous or fp({k:v for k,v in r.items() if k!='record_hash'})!=r['record_hash']:
            errors.append('chain:'+str(p.relative_to(RUN)))
        previous=r['record_hash']
    chains+=1
integrity=dict(chain_journals_checked=chains,chain_errors=errors,
    parent_files_match_continuation=before[str(parent)]==manifest['parent_files'],
    continuation_hash_valid=fp(manifest)==plan['continuation_binding']['sha256'],
    frozen_sources_valid=all(sha(RUN/'frozen_source'/f)==h for f,h in plan['sources'].items()),
    current_source_differences=[f for f,h in plan['sources'].items() if not (ROOT/f).exists() or sha(ROOT/f)!=h],
    input_bindings_valid=all(sha(Path(v['path']))==v['sha256'] for v in plan['cumulative_input_bindings'].values()),
    gate_pool_hash_valid=sha(Path(plan['gate_pool_binding']['path']))==plan['gate_pool_binding']['sha256'],
    task_order_hash_valid=fp(tasks)==plan['tasks_sha256'],
    inherited_prefixes_valid=all(hashlib.sha256((RUN/f).read_bytes()[:v['bytes']]).hexdigest()==v['sha256'] for f,v in manifest['inherited_prefixes'].items()))

states={a:rows(RUN/a/'task_state.jsonl') for a in plan['arms']}
grades={a:{r['payload']['sequence']:r['payload']['verdict'] for r in rs if r['kind']=='PRIVATE_SCORED'} for a,rs in states.items()}
locks={a:{r['payload']['lock']['sequence']:r for r in rs if r['kind']=='ANSWER_LOCKED'} for a,rs in states.items()}
task_results=[]; lock_errors=[]
for i,t in enumerate(tasks,1):
    row=dict(sequence=i,task_id=t['task_id'],source_original_id=lineage[t['task_id']]['source_original_id'],
        research_stratum=lineage[t['task_id']]['research_stratum'],arms={})
    for a in plan['arms']:
        v=grades[a][i];lock=locks[a].get(i);missing=v['status']=='INFRASTRUCTURE_MISSING'
        if not missing:
            rlock=lock['payload']['lock']
            score_row=next(x for x in states[a] if x['kind']=='PRIVATE_SCORED' and x['payload']['sequence']==i)
            if v['locked_sha256']!=rlock['locked_sha256'] or lock['at']>score_row['at'] or fp({k:v for k,v in rlock.items() if k!='locked_sha256'})!=rlock['locked_sha256']:
                lock_errors.append([a,i])
        row['arms'][a]=dict(status=v['status'],correct=v.get('correct'),final_finish_reason=(lock['payload']['lock']['responses'][-1]['finish_reason'] if lock else None))
    task_results.append(row)
save('task_results.json',task_results)
common=[r for r in task_results if all(v['status']!='INFRASTRUCTURE_MISSING' for v in r['arms'].values())]
arm_stats={a:dict(statuses=counter(grades[a][i]['status'] for i in grades[a]),correct=sum(grades[a][r['sequence']]['status']=='CONFIRMED_CORRECT' for r in common),n=len(common)) for a in plan['arms']}
pairs={}
for x,y in [('F','G'),('F','T'),('F','R'),('T','G'),('R','G')]:
    wx=[];wy=[];both=[];neither=[]
    for r in common:
        a=r['arms'][x]['status']=='CONFIRMED_CORRECT';b=r['arms'][y]['status']=='CONFIRMED_CORRECT'
        (both if a and b else wx if a else wy if b else neither).append(r['sequence'])
    n=len(wx)+len(wy);p=min(1,2*sum(math.comb(n,j) for j in range(min(len(wx),len(wy))+1))/2**n) if n else 1
    pairs[x+'-'+y]=dict(n=len(common),x_only=wx,y_only=wy,both_correct=both,neither_confirmed_correct=neither,exact_mcnemar_p=p,net_correct=len(wx)-len(wy),unit='one task; not repeated independent trials')
blocks=[]
for lo,hi in [(1,20),(21,40),(41,50)]:
    group=[r for r in common if lo<=r['sequence']<=hi]
    blocks.append(dict(range=[lo,hi],n=len(group),arms={a:counter(r['arms'][a]['status'] for r in group) for a in plan['arms']}))
strata={s:{a:counter(r['arms'][a]['status'] for r in common if r['research_stratum']==s) for a in plan['arms']} for s in sorted({r['research_stratum'] for r in common})}

prices=plan['budget_freeze']['prices']; responses=[]; send_duplicates=[]; wire_errors=[]; reqs={}; failed_connections=[]; solver_projection_errors=[]
for p in sorted(list(RUN.rglob('requests.jsonl'))+list(RUN.rglob('provider.jsonl'))):
    rel=str(p.relative_to(RUN)); rr=rows(p)
    native={x['payload']['request_id']:x['payload']['response'] for x in rr if x['kind']=='RAW_RESPONSE' and 'request_id' in x['payload']}
    send=C.Counter(r['payload'].get('request_id',r['payload'].get('key')) for r in rr if r['kind']=='SEND_STARTED')
    send_duplicates.extend(dict(file=rel,request_id=k,count=v) for k,v in send.items() if v>1)
    for r in rr:
        q=r['payload']
        if r['kind'] in ['NO_GOLD_REQUEST','SEND_STARTED'] and 'wire' in q:
            if fp(q['wire'])!=q['wire_sha256']:wire_errors.append(rel)
        if r['kind']=='NO_GOLD_REQUEST':
            rid=q['request_id'];reqs[rid]=q
            arm,seq,tid,*rest=rid.split('/');seq=int(seq)
            previous=None
            if rest[-1]=='s1':previous=native[rid[:-2]+'s0']['choices'][0]['message']['content']
            expected=solver_messages(PublicMathTask.parse(tasks[seq-1]),previous,profile='concise-v1')
            if q['wire']['messages']!=expected:solver_projection_errors.append([rid,'MESSAGE_PROJECTION_DIFFERS'])
            score_at=next(x['at'] for x in states[arm] if x['kind']=='PRIVATE_SCORED' and x['payload']['sequence']==seq)
            if r['at']>=score_at:solver_projection_errors.append([rid,'REQUEST_NOT_BEFORE_PRIVATE_SCORE'])
        if 'FAIL' in r['kind'] or 'NOT_SENT' in r['kind'] or 'UNKNOWN' in r['kind']:failed_connections.append(dict(file=rel,kind=r['kind'],payload=q))
        if r['kind']!='RAW_RESPONSE':continue
        raw=q['response'];u=raw.get('usage',{});i=u.get('prompt_tokens',0);o=u.get('completion_tokens',0);hit=u.get('prompt_cache_hit_tokens',0)
        cost=(Decimal(i-hit)*Decimal(str(prices['input_cache_miss_peak_usd_per_million']))+Decimal(hit)*Decimal(str(prices['input_cache_hit_peak_usd_per_million']))+Decimal(o)*Decimal(str(prices['output_peak_usd_per_million'])))/10**6
        rid=q.get('request_id',q.get('key'));arm=rel.split('/')[0]
        channel='learning' if '/learning/' in rel else 'R_extra' if '/r-extra/' in str(rid) or '/extra' in str(rid) else 'base'
        # Native R extra IDs use retry*, distinguish them from base/s0,s1.
        if arm=='R' and channel=='base' and '/base/' not in str(rid):channel='R_extra'
        responses.append(dict(arm=arm,channel=channel,journal=rel,request_id=rid,response_id=raw.get('id'),at=r['at'],model=raw.get('model'),finish_reason=raw.get('choices',[{}])[0].get('finish_reason'),input_tokens=i,output_tokens=o,total_tokens=i+o,cache_hit_tokens=hit,reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),estimated_usd=str(cost),response_sha256=fp(raw)))
save('response_accounting.json',responses)
costs={}
for a in plan['arms']:
    costs[a]={}
    for ch in ['base','learning','R_extra','total']:
        rr=[r for r in responses if r['arm']==a and (ch=='total' or r['channel']==ch)]
        costs[a][ch]=dict(responses=len(rr),input_tokens=sum(r['input_tokens'] for r in rr),output_tokens=sum(r['output_tokens'] for r in rr),tokens=sum(r['total_tokens'] for r in rr),estimated_usd=str(sum((Decimal(r['estimated_usd']) for r in rr),Decimal(0))),finish_reasons=counter(r['finish_reason'] for r in rr))

learning={}; association_audit=[]; chronology_errors=[]; field_errors=[]
for a in ['T','F']:
    d=RUN/a/'cumulative';raws=[r['payload'] for r in rows(d/'raw.jsonl')];facts={r['id']:r for r in raws}
    views=rows(d/'views.jsonl');assoc=[r['payload'] for r in views if r['kind']=='ASSOCIATION_DONE'];clusters=[r['payload'] for r in rows(d/'clusters.jsonl') if r['kind']=='CLUSTER_VERSION'];queue=rows(d/'queue.jsonl')
    aa=[]
    for done in assoc:
        job=next((RUN/a/'learning').glob('*/jobs/'+done['id']))
        frozen=read(job/'input.json');cr=rows(job/'compiler.jsonl');rr=[r['payload']['response'] for r in cr if r['kind']=='GENERATION_RESPONSE'][-1]
        raw=rr['raw_response'];text=raw['choices'][0]['message'].get('content','');findings=[];parsed=None
        try:parsed=json.loads(text)
        except ValueError as e:findings.append(dict(path='$',error='INVALID_JSON',detail=str(e)))
        proposals=[]
        if parsed is not None:
            findings+=fields(parsed,['descriptions','clusters'],'$')
            for n,c in enumerate(parsed.get('clusters',[])):
                path='$.clusters['+str(n)+']'
                findings+=fields(c,['cluster_id','hypothesis','assessment','links'],path)
                for lid, count in C.Counter(l.get('evidence_id') for l in c.get('links',[])).items():
                    if count>1:findings.append(dict(path=path+'.links',error='DUPLICATE_EVIDENCE_ID',id=lid,count=count))
                try:validate_decision(c.get('assessment')); valid=True
                except ValueError as e:valid=False;findings.append(dict(path=path+'.assessment',error='INVALID_ASSESSMENT',detail=str(e)))
                proposals.append(dict(mechanism=c.get('hypothesis',{}).get('mechanism'),cause_status=c.get('assessment',{}).get('mechanism_assessment',{}).get('status'),candidate_decision=c.get('assessment',{}).get('algorithm_candidate',{}).get('decision'),assessment_valid=valid,cluster_id=c.get('cluster_id'),link_roles=[l.get('relation') for l in c.get('links',[])]))
        evidence=frozen['payload']['evidence'];seqs=[e['available_after_sequence'] for e in evidence]
        if any(s>done['cutoff'] for s in seqs):chronology_errors.append([a,done['cutoff'],'future evidence'])
        if a=='T' and any(set(e)!=set(['evidence_id','problem','raw_sha256','available_after_sequence']) for e in evidence):field_errors.append([a,done['cutoff'],'non-task evidence'])
        if a=='F' and any(e.get('correct') is not False or e['evidence_id'] not in facts for e in evidence):field_errors.append([a,done['cutoff'],'non-confirmed failure'])
        sr=max(r['at'] for group in states.values() for r in group if r['kind']=='PRIVATE_SCORED' and r['payload']['sequence']==done['cutoff'])
        req_at=min(r['at'] for r in cr if r['kind']=='GENERATION_REQUESTED')
        if req_at<sr:chronology_errors.append([a,done['cutoff'],'learning before barrier'])
        item=dict(arm=a,cutoff=done['cutoff'],job_id=done['id'],job_path=str(job.relative_to(ROOT)),outcome=done['outcome'],visible_sequences=seqs,input_evidence_count=len(evidence),old_evidence_included=any(s<done['cutoff'] for s in seqs),input_cluster_count=len(frozen['payload']['candidate_clusters']),raw_response_sha256=fp(raw),finish_reason=raw['choices'][0]['finish_reason'],findings=findings,proposals=proposals)
        aa.append(item);association_audit.append(item)
    learning[a]=dict(persisted_records=len(raws),distinct_source_originals=len({r['source_original_id'] for r in raws}),source_sequences=[r['sequence'] for r in raws],association_calls=len(assoc),association_outcomes=counter(r['outcome'] for r in assoc),raw_json_valid=sum(not any(f.get('error')=='INVALID_JSON' for f in x['findings']) for x in aa),accepted_empty_cluster_responses=sum(x['outcome']=='ACCEPTED_UNVERIFIED' and not x['proposals'] for x in aa),accepted_cluster_responses=sum(x['outcome']=='ACCEPTED_UNVERIFIED' and bool(x['proposals']) for x in aa),old_evidence_calls=sum(x['old_evidence_included'] for x in aa),multi_evidence_calls=sum(x['input_evidence_count']>1 for x in aa),cluster_versions=len(clusters),distinct_clusters=len({c['cluster_id'] for c in clusters}),generation_jobs_started=sum(r['kind']=='CUMULATIVE_JOB_STARTED' for r in queue),schedule_skips=counter(r['payload']['skip_reason'] for r in queue if r['kind']=='CUMULATIVE_SCHEDULE'),candidate_requests=0,induction_requests=0,revision_requests=0,job_results=[],cluster_records=clusters)
    for p in (RUN/a/'learning').glob('*/jobs/*/compiler.jsonl'):
        for r in kinds(p,'GENERATION_REQUESTED'):
            if 'association_input' in r['payload']:continue
            learning[a][r['payload']['phase']+'_requests']+=1
    for p in (RUN/a/'learning').glob('*/jobs/*/result.json'):learning[a]['job_results'].append(dict(path=str(p.relative_to(ROOT)),result=read(p)))
save('association_rejections_and_proposals.json',association_audit)
delivery=[]
for a in ['T','F']:
    for p in (RUN/a/'learning').glob('*/jobs/*/compiler.jsonl'):
        rr=rows(p);requested={fp(r['payload']):r['payload'] for r in rr if r['kind']=='GENERATION_REQUESTED'}
        for r in rr:
            if r['kind']!='GENERATION_RESPONSE':continue
            req=requested[r['payload']['request_sha256']]
            if req['phase']!='candidate':continue
            parsed=r['payload']['response'];raw=parsed['raw_response'];choice=raw['choices'][0]
            obj=json.loads(choice['message']['content']);code=obj.get('code','')
            try:
                tree=ast.parse(code);syntax=True
                functions=[n.name for n in tree.body if isinstance(n,ast.FunctionDef)]
                assignments=[t.id for n in tree.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)]
            except SyntaxError:syntax=False;functions=[];assignments=[]
            delivery.append(dict(arm=a,journal=str(p.relative_to(ROOT)),raw_response_sha256=fp(raw),supplier_finish_reason=choice['finish_reason'],adapter_finish_reason=parsed['finish_reason'],delivery_status=parsed.get('delivery_status'),diagnostic=parsed.get('contract_diagnostic'),top_level_fields=list(obj),code_characters=len(code),code_sha256=hashlib.sha256(code.encode()).hexdigest(),read_only_ast_parse=syntax,functions=functions,module_assignments=assignments,worker_executed=False,mathematical_correctness='NOT_EVALUATED',original_response_not_modified=True))
save('candidate_delivery_audit.json',delivery)

accounts=[];pending=[];budget_errors=[]
for p in RUN.rglob('*budget.jsonl'):
    rr=rows(p);b=PersistentBudget.__new__(PersistentBudget);b.path=p;b.config=rr[0]['payload']['config'];st,_=b._state(rr);total=b._totals(rr)
    accounts.append(dict(path=str(p.relative_to(RUN)),totals=total,config=b.config))
    for rid,v in st.items():
        if v['status'] not in ('settled','not_sent'):pending.append(dict(ledger=str(p.relative_to(RUN)),request_id=rid,state=v))
    for field,limit in [('calls','max_calls'),('tokens','max_tokens'),('cost','max_cost_microusd'),('tools','max_tools')]:
        if field in total and total[field]>b.config[limit]:budget_errors.append([str(p),field,total[field],b.config[limit]])
save('ledger_audit.json',dict(accounts=accounts,pending=pending,budget_errors=budget_errors))

same_initial={i:len({reqs[f'{a}/{i}/{tasks[i-1]["task_id"]}/base/s0']['wire_sha256'] for a in plan['arms']})==1 for i in range(1,51)}
integrity.update(answer_lock_and_score_errors=lock_errors,chronology_errors=chronology_errors,learning_projection_errors=field_errors,solver_projection_and_score_order_errors=solver_projection_errors,solver_request_messages_checked=len(reqs),duplicate_sends=send_duplicates,duplicate_provider_response_ids=[x for x,n in C.Counter(r['response_id'] for r in responses).items() if n>1],wire_hash_errors=wire_errors,same_initial_wire_tasks=sum(same_initial.values()),solver_gold_flags_false=all(v.get('gold_exposed') is False for v in reqs.values()),budget_errors=budget_errors)
completed=kinds(RUN/'stream.jsonl','STREAM_COMPLETED')[-1]
tz=ZoneInfo('America/New_York')
result=dict(scope='READ_ONLY_POSTHOC_ANALYSIS_NO_API_NO_NEW_SCORING',run=str(RUN),protocol_sha256=fp(plan),parent_protocol_sha256=manifest['parent_protocol_sha256'],
    run_start_time_et=datetime.fromtimestamp(min(r['at'] for r in rows(RUN/'stream.jsonl')),tz).isoformat(),run_complete_time_et=datetime.fromtimestamp(completed['at'],tz).isoformat(),
    completion=completed['payload'],progress=read(RUN/'progress.json'),task_count=50,common_task_count=len(common),
    provenance=dict(distinct_original_ids=len({v['source_original_id'] for v in lineage.values()}),distinct_lineage_ids=len({v['lineage_id'] for v in lineage.values()}),strata=counter(v['research_stratum'] for v in lineage.values()),mechanism_family=counter(v['mechanism_family'] for v in lineage.values())),
    integrity=integrity,arms=arm_stats,pairs=pairs,blocks=blocks,strata=strata,costs=costs,learning=learning,
    response_count=len(responses),tokens=sum(r['total_tokens'] for r in responses),estimated_usd=str(sum((Decimal(r['estimated_usd']) for r in responses),Decimal(0))),
    network=dict(after_continuation_responses=sum(r['at']>next(x['at'] for x in rows(RUN/'stream.jsonl') if x['kind']=='CONTINUATION_IMPORTED') for r in responses),connection_attempts=sum(len(kinds(p,'CONNECT_ATTEMPT')) for p in RUN.rglob('*budget.jsonl')),isolations=manifest['isolations'],pending_requests=len(pending),no_new_unknown=len(pending)==1 and pending[0]['request_id']==manifest['isolations'][0]['request_id']),
    retry_credits=[r['payload'] for r in states['R'] if r['kind']=='RETRY_CREDIT'],original_summary=old_summary)
assert result['response_count']==old_summary['responses']
assert result['tokens']==old_summary['tokens']
assert abs(float(result['estimated_usd'])-old_summary['estimated_peak_usd'])<1e-10
assert all(arm_stats[a]['correct']==old_summary['arms'][a]['statuses']['CONFIRMED_CORRECT'] for a in plan['arms'])
after={str(p):files(p) for p in [RUN,parent]}
assert before==after,'analysis mutated source evidence'
result['integrity']['run_and_parent_unchanged_during_analysis']=True
save('input_manifest.json',before)
save('analysis.json',result)
print(json.dumps({k:result[k] for k in ['completion','integrity','costs','response_count','tokens','estimated_usd','network']},ensure_ascii=False,indent=2))
