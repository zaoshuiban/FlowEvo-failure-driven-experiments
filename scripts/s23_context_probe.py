"""Exploratory manually specified input operator; not learned or deployed."""
import ast,copy,io,json,pathlib,sys,time,tokenize
import s22_executor as e
from failure_evo.workflow_protocol_v2 import prepare,delivery,SharedTransport
from failure_evo.runtime import Budget
ROOT=e.ROOT;RUN=ROOT/'runs/s23_context_probe_20261026_01'
ADVICE='Deliver a complete executable solution now. Keep comments concise and factual. Do not put extended derivations, self-dialogue, or unfinished alternatives inside code comments.'
ARMS=['G','P','C','CP']
def strip_comments(code):
    before=ast.parse(code);tokens=list(tokenize.generate_tokens(io.StringIO(code).readline))
    clean=tokenize.untokenize([(t.type,t.string) for t in tokens if t.type!=tokenize.COMMENT])
    assert ast.dump(before,include_attributes=False)==ast.dump(ast.parse(clean),include_attributes=False)
    def semantic_tokens(c):return [(t.type,t.string) for t in tokenize.generate_tokens(io.StringIO(c).readline) if t.type not in (tokenize.COMMENT,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.ENDMARKER)]
    assert semantic_tokens(code)==semantic_tokens(clean)
    return clean

def prepare_run():
    e.verify();RUN.mkdir(exist_ok=False);inventory=[];selected=[]
    for i in range(1,11):
        f=e.read(e.BASE/f'frozen/{i:02}.json');p=f['public_checkpoint'];code=p['code'];item=dict(index=i,task_id=p['task_id'],image_placeholder='[Image]' in p['task_public']['prompt'],characters=len(code))
        try:
            clean=strip_comments(code);comments=sum(len(t.string) for t in tokenize.generate_tokens(io.StringIO(code).readline) if t.type==tokenize.COMMENT)
            item.update(ast_preserved=True,comment_ratio=comments/max(1,len(code)),clean_characters=len(clean))
        except (SyntaxError,tokenize.TokenError,IndentationError) as ex:item.update(ast_preserved=False,error=type(ex).__name__)
        eligible=item['ast_preserved'] and not item['image_placeholder'] and item['characters']>=1000 and item['comment_ratio']>=.2
        item['eligible']=eligible;inventory.append(item)
        if eligible and len(selected)<2:
            entry=dict(index=i,task_id=p['task_id'],checkpoint=p,requests={})
            for arm in ARMS:
                body=copy.deepcopy(f['request_freeze']['arms']['A']['wire'])
                if arm in ('C','CP'):
                    context=json.loads(body['messages'][1]['content']);context['candidate_code']=strip_comments(context['candidate_code']);body['messages'][1]['content']=e.canonical(context)
                if arm in ('P','CP'):body['messages'][-1]['content']+='\n'+ADVICE
                req=prepare(body['messages'],temperature=0)
                assert req.input_upper+req.output_upper<=p['checkpoint_budget']['max_tokens']-p['checkpoint_budget']['used_tokens']
                entry['requests'][arm]=dict(wire=req.body,hash=req.sha256,input_upper=req.input_upper,output_upper=req.output_upper)
            entry['order']=ARMS if len(selected)==0 else list(reversed(ARMS));selected.append(entry)
    assert len(selected)==2
    plan=dict(version='s23-context-factorial-v1',role='post-hoc developer mechanism probe; no learned Operator',selection='S22 frozen order; AST parseable; >=1000 characters; >=20% comment characters; no literal [Image]; first two; no new model outcome selection',exposure='S22 outcomes previously exposed; exploratory only',arms=dict(G='unchanged S22 A request',P='G plus generic delivery advice',C='G with comment removal only',CP='both'),hard_usd=.4,max_calls=8,model='deepseek-flash',output_limit=8192,input_upper=32768,source_hash=e.sha(__file__),base_protocol_hash=e.read(e.BASE/'protocol.json')['protocol_hash'],tasks=selected,inventory=inventory,api_authorization_basis='User requests exploratory experiments; previous standing instruction allows small new API validations without asking; new independent bounded budget, no S22 balance reuse',stops='unknown/model/usage/hash mismatch; Worker error; hard budget; never resend',success_criterion='public AND locked same-task review pass; partial pass, shorter output and two failures are not efficiency successes',inference='manual intervention headroom only; no independent generalization, no causal learning attribution',next_step='Only if context transform adds reliable value over P consider automatic induction and independent programs; otherwise stop this probe')
    plan['protocol_hash']=e.fingerprint(plan);e.save(RUN/'protocol.json',plan)
    e.save(RUN/'authorization.json',dict(run_id=RUN.name,protocol_hash=plan['protocol_hash'],max_calls=8,max_cost_microusd=400000,api_spend_authorized=True,basis=plan['api_authorization_basis']))
    print('FROZEN',[(x['index'],x['task_id']) for x in selected],sum(v['input_upper']+v['output_upper'] for t in selected for v in t['requests'].values())*1.2/1e6)

def budget(p):return e.ScopedBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=p['protocol_hash'],max_calls=8,max_tokens=327680,max_tools=1000,max_cost_microusd=400000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=12000000,tool_milliseconds_upper=20000,wall_seconds=21600)
def execute():
    import fcntl
    p=e.read(RUN/'protocol.json');assert e.sha(__file__)==p['source_hash'];assert e.fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})==p['protocol_hash'];e.verify()
    a=e.read(RUN/'authorization.json');assert a['api_spend_authorized'] is True and a['protocol_hash']==p['protocol_hash'] and a['max_cost_microusd']==400000
    with (RUN/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (RUN/'state.json').exists():raise RuntimeError('no automatic rerun')
        b=budget(p);judge=e.worker(b,RUN);state=dict(status='RUNNING',rows=[]);e.save(RUN/'state.json',state)
        try:
            for t in p['tasks']:
                for arm in t['order']:
                    key=str(t['index'])+'-'+arm;f=t['requests'][arm];req=prepare(f['wire']['messages'],temperature=0);assert req.sha256==f['hash']
                    cp=t['checkpoint']['checkpoint_budget'];task=Budget(max_calls=cp['calls']+1,max_tokens=cp['max_tokens'],max_tools=cp['max_tools'],calls=cp['calls'],used_tokens=cp['used_tokens'],tool_calls=cp['tool_calls'],wall_seconds=min(600,cp['remaining_seconds']))
                    row=dict(key=key,index=t['index'],arm=arm,task_id=t['task_id'],state='INTENT');state['rows'].append(row);e.save(RUN/'state.json',state)
                    def sender(w):
                        assert e.hashlib.sha256(w).hexdigest()==f['hash'];raw=e.real_sender(w,min(90,task.remaining_seconds));e.save(RUN/(key+'.raw.json'),raw);return raw
                    audit=[];tr=SharedTransport(b,sender,authorized=dict(run_id=RUN.name,protocol_hash=p['protocol_hash']),audit=audit);start=time.monotonic()
                    try:res=tr.send(req,request_id=key,capability='s23-context-probe',task_budget=task)
                    finally:e.save(RUN/(key+'.transport.json'),audit)
                    row.update(state='RESPONSE_RECEIVED',response=res,request_seconds=time.monotonic()-start);e.save(RUN/'state.json',state)
                    artifact=delivery(res['text'],res['finish_reason']);e.save(RUN/(key+'.artifact.json'),artifact)
                    b.task_scope=task;scored=judge(t['task_id'],artifact['code'],t['checkpoint']['public_cases']);b.task_scope=None
                    if task.remaining_seconds<=0:raise TimeoutError('branch deadline')
                    row.update(state='COMPLETE',public_result=scored,artifact={k:v for k,v in artifact.items() if k!='code'});e.save(RUN/'state.json',state)
            state.update(status='ONLINE_LOCKED',budget=b.snapshot());e.save(RUN/'state.json',state)
        except BaseException as ex:
            state.update(status='STOPPED',exception=type(ex).__name__,budget=b.snapshot());e.save(RUN/'state.json',state);raise
    print('ONLINE_LOCKED')
def review():
    p=e.read(RUN/'protocol.json');s=e.read(RUN/'state.json');assert s['status']=='ONLINE_LOCKED'
    if (RUN/'review.json').exists():raise RuntimeError('review already exists')
    for f,h in e.read(e.BASE/'protocol.json')['evaluator_sources'].items():assert e.sha(ROOT/f)==h
    b=budget(p);judge=e.worker(b,RUN);manifest=e.read(e.BASE/'scoring_manifest.json');rows=[]
    for row in s['rows']:
        descriptor=next(x for x in manifest['rows'] if x['task_id']==row['task_id']);raw=e.read(ROOT/descriptor['evaluator_ref']);cases=raw[row['task_id']]['audit_cases'] if isinstance(raw,dict) else next(x for x in raw if x['task_id']==row['task_id']).get('cases')
        artifact=e.read(RUN/(row['key']+'.artifact.json'));result=judge(row['task_id'],artifact['code'],cases);rows.append(dict(key=row['key'],sealed=result,strict_pass=row['public_result']['passed'] and result['passed']));e.save(RUN/'review_partial.json',rows)
    e.save(RUN/'review.json',dict(rows=rows,budget=b.snapshot()));print('REVIEW_COMPLETE')
if __name__=='__main__':{'prepare':prepare_run,'execute':execute,'review':review}[sys.argv[1]]()
