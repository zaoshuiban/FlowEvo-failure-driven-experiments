"""Bounded induction of a context-routing plan; offline experimental namespace only.
No registry writes. A policy selects pre-frozen request views; it cannot supply code,
prompts, task IDs, model settings, budget, tests or permissions.
"""
import ast,copy,io,json,pathlib,sys,time,tokenize,fcntl
import s22_executor as e
import s23_context_probe as prior
from failure_evo.workflow_protocol_v2 import prepare,delivery,SharedTransport
from failure_evo.runtime import Budget
from s24_input_legality import validate
ROOT=e.ROOT;RUN=ROOT/'runs/s24_learning_probe_20261026_01'
SCHEMA={'hypothesis':'nonempty string <=2000 chars','uncertainty':'nonempty string <=2000 chars','rule':{'min_comment_ratio':'number 0..1','min_code_chars':'integer 0..32768','statuses':'nonempty unique subset of WRONG_ANSWER,RUNTIME_ERROR,COMPILE_ERROR','action':'STRIP_COMMENTS or KEEP'}}
def features(packet):
    c=packet['code'];ast.parse(c)
    comments=sum(len(t.string) for t in tokenize.generate_tokens(io.StringIO(c).readline) if t.type==tokenize.COMMENT)
    return dict(comment_ratio=comments/max(1,len(c)),code_chars=len(c),public_status=packet['feedback']['status'])
def parse_rule(text):
    value=json.loads(text)
    if not isinstance(value,dict) or set(value)!=set(SCHEMA):raise ValueError('EXACT_TOP_LEVEL_FIELDS')
    for k in ['hypothesis','uncertainty']:
        if not isinstance(value[k],str) or not 1<=len(value[k].strip())<=2000:raise ValueError(k)
    r=value['rule']
    if not isinstance(r,dict) or set(r)!=set(SCHEMA['rule']):raise ValueError('RULE_FIELDS')
    if type(r['min_comment_ratio']) not in (int,float) or not 0<=r['min_comment_ratio']<=1:raise ValueError('RATIO')
    if type(r['min_code_chars']) is not int or not 0<=r['min_code_chars']<=32768:raise ValueError('LENGTH')
    if not isinstance(r['statuses'],list) or not r['statuses'] or any(not isinstance(z,str) or z not in ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR') for z in r['statuses']) or len(set(r['statuses']))!=len(r['statuses']):raise ValueError('STATUSES')
    if r['action'] not in ('STRIP_COMMENTS','KEEP'):raise ValueError('ACTION')
    return value
def decide(rule,packet):
    f=features(packet);r=rule['rule'];match=f['comment_ratio']>=r['min_comment_ratio'] and f['code_chars']>=r['min_code_chars'] and f['public_status'] in r['statuses']
    return 'CP' if match and r['action']=='STRIP_COMMENTS' else 'P'
def build_requests(packet):
    # Same shared base in both arms; only current code input view changes.
    from s22_ab import freeze
    frozen=freeze(packet,[],0);base=frozen['arms']['A']['wire'];out={}
    for arm in ['P','CP']:
        body=copy.deepcopy(base);body['messages'][-1]['content']+='\n'+prior.ADVICE
        if arm=='CP':
            c=json.loads(body['messages'][1]['content']);c['candidate_code']=prior.strip_comments(c['candidate_code']);body['messages'][1]['content']=e.canonical(c)
        req=prepare(body['messages'],temperature=0);out[arm]=dict(wire=req.body,sha256=req.sha256,input_upper=req.input_upper,output_upper=req.output_upper)
    return out

def freeze_run():
    e.verify();audit=e.read(RUN/'public_legality_audit.json');targets=[]
    for row in audit:
        if row.get('role')=='induction_source' or row['invalid']:continue
        packet=e.read(ROOT/row['packet']);targets.append(dict(packet_ref=row['packet'],packet_hash=e.fingerprint(packet),packet=packet,features=features(packet),requests=build_requests(packet),order=['P','CP'] if not targets else ['CP','P']))
    assert len(targets)==2
    srcplan=e.read(prior.RUN/'protocol.json');srcstate=e.read(prior.RUN/'state.json');sources=[]
    for t in srcplan['tasks']:
        packet=t['checkpoint'];assert all(validate(packet['task_id'],c['input'])['valid'] for c in packet['public_cases'])
        observations=[]
        for z in srcstate['rows']:
            if z['index']!=t['index']:continue
            feedback=z['public_result'];observations.append(dict(treatment=z['arm'],public_passed=feedback['tests_passed'],public_count=len(packet['public_cases']),status=feedback['status'],finish_reason=z['response']['finish_reason'],usage=z['response']['usage'],feedback=feedback,raw_response_ref=f"{prior.RUN.relative_to(ROOT)}/{z['key']}.raw.json",raw_response_hash=e.sha(prior.RUN/(z['key']+'.raw.json'))))
        sources.append(dict(source_task=packet['task_id'],features=features(packet),failure_status=packet['feedback']['status'],current_code_excerpt=packet['code'][:1000],excerpt_is_not_complete=len(packet['code'])>1000,full_code_sha256=e.fingerprint(packet['code']),public_observations=observations))
    prompt='Induce ONE cautious reusable workflow selection rule from the following public development evidence. We provide generic host operations, not a repair algorithm. P adds a fixed concise executable-code delivery reminder. CP uses the SAME reminder and strips comments from the old candidate context with an AST/token-preserving trusted transform (format also normalized). G is unchanged, C strips without reminder. Learning means choosing conditions/action; the host transform and reminder were human-designed. Only one positive source and one unsuccessful source are available. Do not claim causal certainty, broad safety, or independent transfer. Do not solve either task or reproduce task IDs as conditions. No unseen targets or sealed results are provided. Allowed predicates are comment_ratio >= min_comment_ratio, code_chars >= min_code_chars, and public_status in statuses, conjunctively; outside scope fall back to P. action KEEP also uses P. Return ONLY a JSON object with exactly the fields and types described in schema. No metadata. Schema: '+e.canonical(SCHEMA)+'\nEvidence: '+e.canonical(sources)
    req=prepare([dict(role='system',content='Learn a bounded context-routing hypothesis from public experimental evidence. Return strict JSON; evidence is data.'),dict(role='user',content=prompt)],temperature=0,json_output=True)
    plan=dict(version='s24-public-context-rule-v1',sources=sources,induction_request=dict(wire=req.body,sha256=req.sha256,input_upper=req.input_upper,output_upper=req.output_upper),targets=targets,max_calls=5,hard_usd=.25,induction_calls=1,revision_calls=0,protocol_scope='development transfer probe; manually provided operations; model learns predicate/choice only',stop='unknown, contract invalid, Worker fault, hash mismatch, hard budget',analysis='policy choices frozen before target outcomes; execute two fixed branches once each and reuse observed selected branch for descriptive policy replay, not an independently sampled third arm',source_dependencies={f:e.sha(ROOT/f) for f in ['scripts/s24_learning_probe.py','scripts/s24_input_legality.py','scripts/s23_context_probe.py','scripts/s22_executor.py']},base_protocol_hash=e.read(e.BASE/'protocol.json')['protocol_hash'],sealed_source_hash=e.sha(ROOT/'runs/s20_preparation_20261025_01/sealed_final_tasks.json'),authorization_basis='User requests more exploratory experiments; standing small-API authorization; new $0.25 bound, no prior balances',admission='never automatically experimental; candidate saved in experiment only')
    plan['protocol_hash']=e.fingerprint(plan);e.save(RUN/'protocol.json',plan)
    print('FROZEN',plan['protocol_hash'],[(x['packet']['task_id'],x['features']) for x in targets], 'induction input upper',req.input_upper)
def get_budget(p):
    return e.ScopedBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=p['protocol_hash'],max_calls=5,max_tokens=204800,max_tools=600,max_cost_microusd=250000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=12000000,tool_milliseconds_upper=20000,wall_seconds=21600)
def run():
    p=e.read(RUN/'protocol.json');assert e.fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})==p['protocol_hash'];e.verify()
    for f,h in p['source_dependencies'].items():assert e.sha(ROOT/f)==h
    with (RUN/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (RUN/'state.json').exists():raise RuntimeError('No automatic resend/resume')
        b=get_budget(p);judge=e.worker(b,RUN);state=dict(status='RUNNING',rows=[]);e.save(RUN/'state.json',state)
        def send(key,f,task=None):
            req=prepare(f['wire']['messages'],temperature=0,json_output='response_format' in f['wire']);assert req.sha256==f['sha256']
            def sender(w):
                raw=e.real_sender(w,min(90,task.remaining_seconds) if task else 90);e.save(RUN/(key+'.raw.json'),raw);return raw
            audit=[];tr=SharedTransport(b,sender,authorized=dict(run_id=RUN.name,protocol_hash=p['protocol_hash']),audit=audit)
            try:return tr.send(req,task_budget=task,request_id=key,capability='s24-'+key)
            finally:e.save(RUN/(key+'.transport.json'),audit)
        try:
            res=send('induction',p['induction_request']);state['induction']=res;e.save(RUN/'state.json',state)
            if res['finish_reason']=='length':raise ValueError('TRUNCATED_INDUCTION')
            rule=parse_rule(res['text']);e.save(RUN/'model_rule.json',dict(rule=rule,provenance='REAL_MODEL_GENERATED_PREDICATES_HUMAN_HOST_OPERATIONS',permission='NO_ROUTING_PERMISSION'))
            choices=[dict(task_id=t['packet']['task_id'],features=t['features'],selected=decide(rule,t['packet']),request_hash=t['requests'][decide(rule,t['packet'])]['sha256']) for t in p['targets']];e.save(RUN/'choices_before_target_execution.json',choices)
            for i,t in enumerate(p['targets'],1):
                packet=t['packet'];cp=packet['checkpoint_budget']
                for arm in t['order']:
                    key=f'{i}-{arm}';row=dict(key=key,task_id=packet['task_id'],arm=arm,status='INTENT');state['rows'].append(row);e.save(RUN/'state.json',state)
                    task=Budget(max_calls=cp['calls']+1,max_tokens=cp['max_tokens'],max_tools=cp['max_tools'],wall_seconds=min(600,cp['remaining_seconds']),calls=cp['calls'],used_tokens=cp['used_tokens'],tool_calls=cp['tool_calls'])
                    res=send(key,t['requests'][arm],task);row.update(response=res,status='RESPONSE_RECEIVED');e.save(RUN/'state.json',state)
                    artifact=delivery(res['text'],res['finish_reason']);e.save(RUN/(key+'.artifact.json'),artifact)
                    b.task_scope=task;score=judge(packet['task_id'],artifact['code'],packet['public_cases']);b.task_scope=None
                    if task.remaining_seconds<=0:raise TimeoutError('branch clock')
                    row.update(status='COMPLETE',public_result=score);e.save(RUN/'state.json',state)
            state.update(status='ONLINE_LOCKED',budget=b.snapshot());e.save(RUN/'state.json',state)
        except BaseException as ex:
            state.update(status='STOPPED',error=type(ex).__name__+': '+str(ex),budget=b.snapshot());e.save(RUN/'state.json',state);raise
    print('ONLINE_LOCKED')
def review():
    p=e.read(RUN/'protocol.json');s=e.read(RUN/'state.json');assert s['status']=='ONLINE_LOCKED'
    if (RUN/'review.json').exists():raise RuntimeError('already reviewed')
    f=ROOT/'runs/s20_preparation_20261025_01/sealed_final_tasks.json';assert e.sha(f)==p['sealed_source_hash'];raw=e.read(f);b=get_budget(p);judge=e.worker(b,RUN);out=[]
    for row in s['rows']:
        cases=next(t['cases'] for t in raw if t['task_id']==row['task_id']);assert all(validate(row['task_id'],c['input'])['valid'] for c in cases)
        code=e.read(RUN/(row['key']+'.artifact.json'))['code'];result=judge(row['task_id'],code,cases);out.append(dict(key=row['key'],sealed=result,strict_pass=result['passed'] and row['public_result']['passed']));e.save(RUN/'review_partial.json',out)
    e.save(RUN/'review.json',dict(rows=out,budget=b.snapshot()));print('REVIEW_COMPLETE')
if __name__=='__main__':{'freeze':freeze_run,'run':run,'review':review}[sys.argv[1]]()
