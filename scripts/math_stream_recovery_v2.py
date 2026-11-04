"""Opt-in network isolation and lineage-aware accounting; old runs are read-only."""
import http.client, ssl, time, fcntl, json, collections
from pathlib import Path
from failure_evo import math_stream as ms
from failure_evo.math_stream import StreamRuntime, read, save, sha
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import RunUnhealthy
from resume_math_stream200_after89 import Continuation

NETWORK_TYPES=(TimeoutError,http.client.RemoteDisconnected,ConnectionResetError,ssl.SSLEOFError,http.client.IncompleteRead)
NETWORK_NAMES={t.__name__ for t in NETWORK_TYPES}

def account(path):
    b=PersistentBudget.__new__(PersistentBudget);b.path=Path(path)
    with b._locked() as rows:
        states,_=b._state(rows)
        return rows[0]['payload'],states,b._totals(rows)

class ResilientStream(StreamRuntime):
    def quarantines(self):return [r['payload'] for r in EvidenceStore(self.path/'network_isolation.jsonl').records() if r['kind']=='NETWORK_ISOLATED']
    def missing(self):return set(self.plan['recovery']['inherited_missing'])|{q['sequence'] for q in self.quarantines()}
    def validate_isolation(self,q):
        if q['exception_type'] not in NETWORK_NAMES:raise RunUnhealthy('isolation exception not allowed')
        seq=q['sequence'];arm=q['arm'];rid=q['request_id']
        if type(seq)!=int or not self.plan['recovery']['start']<=seq<=len(self.tasks) or arm not in ms.ARMS:raise RunUnhealthy('isolation identity')
        if not rid.startswith(f'{arm}/{seq}/{self.tasks[seq-1].task_id}/'):raise RunUnhealthy('isolation request/task mismatch')
        expected=f'{arm}/solve_budget.jsonl'
        if q['ledger']!=expected:raise RunUnhealthy('only solver transport can be isolated')
        _,states,_=account(self.path/expected);state=states.get(rid,{})
        if state.get('status')!='unknown' or state.get('request_hash')!=q['wire_sha256']:raise RunUnhealthy('isolation ledger mismatch')
        records=self.arms[arm]['client'].channel.events.records()
        rr=[r for r in records if r['payload'].get('request_id')==rid]
        if sum(r['kind']=='SEND_STARTED' for r in rr)!=1 or any(r['kind']=='RAW_RESPONSE' for r in rr):raise RunUnhealthy('received/duplicate request cannot be network isolated')
        req=[r['payload'] for r in rr if r['kind']=='NO_GOLD_REQUEST']
        if len(req)!=1 or req[0]['wire_sha256']!=q['wire_sha256']:raise RunUnhealthy('isolation wire mismatch')
        finished=[r['payload'] for r in rr if r['kind']=='REQUEST_FINISHED']
        if not finished or finished[-1].get('audit',[])[-1].get('status')!='UNKNOWN':raise RunUnhealthy('incomplete transport audit')
        for a in self.arms.values():
            if any(r['kind']=='PRIVATE_SCORED' and r['payload']['sequence']==seq and r['payload']['verdict']['status']!='INFRASTRUCTURE_MISSING' for r in a['states'].records()):raise RunUnhealthy('cannot isolate after scoring')
    def health(self):
        if fingerprint(self.plan)!=self.ph:raise RunUnhealthy('protocol drift')
        if time.time()>=self.plan['recovery']['expires_at']:raise RunUnhealthy('inherited wall budget expired')
        root=Path(__file__).resolve().parents[1]
        for rel,h in self.plan['sources'].items():
            if sha(root/rel)!=h:raise RunUnhealthy('frozen source changed: '+rel)
        qs=self.quarantines()
        if len(qs)>self.plan['recovery']['max_new_isolations']:raise RunUnhealthy('isolation count ceiling')
        for q in qs:self.validate_isolation(q)
        allowed={(q['ledger'],q['request_id']) for q in qs}
        for p in self.path.rglob('*budget.jsonl'):
            _,states,_=account(p)
            for k,s in states.items():
                if s['status']!='settled' and (str(p.relative_to(self.path)),k) not in allowed:raise RunUnhealthy('unclassified pending/unknown '+k)
        for p in self.path.rglob('provider.jsonl'):
            rr=EvidenceStore(p).records();start={r['payload']['key'] for r in rr if r['kind']=='SEND_STARTED'};got={r['payload']['key'] for r in rr if r['kind']=='RAW_RESPONSE'}
            if start-got or any(r['kind']=='SEND_UNKNOWN' for r in rr):raise RunUnhealthy('learning transport unknown')
    def mark_missing(self,seq):
        task=self.tasks[seq-1]
        for arm,a in self.arms.items():
            self.emit_once(a['states'],'PRIVATE_SCORED',f'{arm}/{seq}/{task.task_id}',dict(task_id=task.task_id,sequence=seq,verdict=dict(status='INFRASTRUCTURE_MISSING',correct=None,credible_failure=False,reason='NETWORK_ISOLATION_NO_MATH_EVALUATION')))
    def isolate(self,seq,arm,exc):
        if type(exc) not in NETWORK_TYPES:raise exc
        if len(self.quarantines())>=self.plan['recovery']['max_new_isolations']:raise RunUnhealthy('isolation ceiling reached; new UNKNOWN retained') from exc
        _,states,_=account(self.path/arm/'solve_budget.jsonl')
        known={q['request_id'] for q in self.quarantines()}
        new=[(k,v) for k,v in states.items() if v['status']=='unknown' and k not in known]
        if len(new)!=1:raise RunUnhealthy('ambiguous network request') from exc
        rid,state=new[0]
        q=dict(sequence=seq,arm=arm,ledger=f'{arm}/solve_budget.jsonl',request_id=rid,wire_sha256=state['request_hash'],exception_type=type(exc).__name__,exception_reason=str(exc),reservation_unchanged=True,no_retry=True)
        self.validate_isolation(q)
        EvidenceStore(self.path/'network_isolation.jsonl').append('NETWORK_ISOLATED',q,time.time())
        self.mark_missing(seq);self.health()
        if seq-1 in self.missing():raise RunUnhealthy('consecutive missing tasks: stop before more requests')
    def evidence(self,arm,cutoff):
        a=self.arms[arm];tasks={t.task_id:t for t in self.tasks};out=[]
        locks={r['payload']['id']:r['payload']['lock'] for r in a['states'].records() if r['kind']=='ANSWER_LOCKED'}
        for r in a['states'].records():
            p=r['payload']
            if r['kind']!='PRIVATE_SCORED' or p['sequence'] in self.missing() or p['sequence']>cutoff or p['verdict']['status']!='CONFIRMED_WRONG':continue
            l=locks[p['id']]
            if not l['responses'] or l['responses'][-1]['finish_reason']!='stop':continue
            out.append(dict(event_id=fingerprint([p['id'],p['verdict']['locked_sha256']]),sequence=p['sequence'],task=tasks[p['task_id']].to_dict(),correct=False,final_output=l['final_output'],trajectory=l['responses'],locked_sha256=l['locked_sha256']))
        return out
    def history_packet(self,arm,cutoff):
        packet,refs=super().history_packet(arm,cutoff)
        bad={self.tasks[i-1].task_id for i in self.missing()};problems={t.problem for t in self.tasks if t.task_id in bad}
        packet['questions']=[q for q in packet['questions'] if q['problem'] not in problems]
        if arm=='F':packet['observations']=[o for o in packet['observations'] if o['problem'] not in problems]
        removed=[t for t in refs['task_ids'] if t in bad];refs['task_ids']=[t for t in refs['task_ids'] if t not in bad];refs['omitted_task_ids']+=removed
        return packet,refs
    def run(self):
        with (self.path/'stream.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            # A crash after writing an isolation receipt can only finish its missing markers.
            self.health()
            for q in self.quarantines():self.mark_missing(q['sequence'])
            if any(i-1 in self.missing() for i in self.missing() if i>=self.plan['recovery']['start']):raise RunUnhealthy('consecutive missing tasks remain a global stop')
            for seq in range(self.plan['recovery']['start'],len(self.tasks)+1):
                task=self.tasks[seq-1];locks={}
                if seq not in self.missing():
                    order=ms.ARMS[(seq-1)%4:]+ms.ARMS[:(seq-1)%4]
                    for arm in order:
                        self.health()
                        try:locks[arm]=self.solve(arm,task,seq)
                        except NETWORK_TYPES as exc:
                            self.isolate(seq,arm,exc);print(f'ISOLATED task {seq}: {type(exc).__name__}; no resend; reservation retained',flush=True);break
                    if seq not in self.missing():
                        for arm in ms.ARMS:
                            a=self.arms[arm];v=a['scorer'].score(task,locks[arm])
                            self.emit_once(a['states'],'PRIVATE_SCORED',f'{arm}/{seq}/{task.task_id}',dict(task_id=task.task_id,sequence=seq,verdict=v))
                        print(f'Task {seq}/{len(self.tasks)} locked and scored in all four arms',flush=True)
                if seq%self.plan['window']==0 or seq==len(self.tasks):
                    for arm in ('T','F'):
                        if seq<len(self.tasks):self.arms[arm]['learner'].learn(seq)
                    for a in self.arms.values():self.emit_once(a['states'],'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    self.emit_once(self.events,'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                save(self.path/'progress.json',dict(last_original_sequence=seq,completed_comparable_tasks=seq-len([i for i in self.missing() if i<=seq]),missing_sequences=sorted(self.missing()),status='COMPLETE_WITH_MISSING' if seq==len(self.tasks) else 'RUNNING'))
            self.emit_once(self.events,'STREAM_COMPLETED','complete',dict(tasks=len(self.tasks)-len(self.missing()),missing=sorted(self.missing()),paid_api=not self.engineering,protocol_amended=True))

def report_chain(roots,out):
    """Read-only chain aggregation: copied learning receipts/accounts counted once."""
    roots=list(map(Path,roots));out=Path(out);accounts={};responses={};http={};unmetered={};increment=[]
    for root in roots:
        before=len(responses)
        for p in root.rglob('*budget.jsonl'):
            opened,states,_=account(p);run=opened['config']['run_id']
            for rid,state in states.items():
                key=(run,rid)
                if key in accounts and accounts[key]['state']!=state:raise ValueError('conflicting inherited budget state')
                accounts.setdefault(key,dict(run_id=run,request_id=rid,state=state,first_seen=str(p)))
        for p in list(root.rglob('requests.jsonl'))+list(root.rglob('provider.jsonl')):
            for r in EvidenceStore(p).records():
                if r['kind']!='RAW_RESPONSE':continue
                raw=r['payload']['response'];key=raw.get('id') or fingerprint(raw)
                if raw.get('http_status'):http.setdefault(key,raw);continue
                if key in responses and responses[key]['response_sha256']!=fingerprint(raw):raise ValueError('response identity collision')
                if key in responses:continue
                u=raw.get('usage')
                if not isinstance(u,dict) or not all(k in u for k in ('prompt_tokens','completion_tokens','total_tokens')):
                    unmetered.setdefault(key,dict(response_sha256=fingerprint(raw),first_seen=str(p)));continue
                i=u['prompt_tokens'];o=u['completion_tokens'];hit=u.get('prompt_cache_hit_tokens',0)
                if u['total_tokens']!=i+o:raise ValueError('usage total mismatch')
                if not all(type(x)==int and x>=0 for x in (i,o,hit)) or hit>i:raise ValueError('usage contract')
                responses[key]=dict(response_id=key,response_sha256=fingerprint(raw),input_tokens=i,output_tokens=o,estimated_peak_usd=((i-hit)*.3+hit*.006+o*1.2)/1e6,first_seen=str(p))
        increment.append(dict(root=str(root),new_unique_responses=len(responses)-before))
    last=roots[-1];maps={};arms={}
    for arm in ms.ARMS:
        rows=EvidenceStore(last/arm/'task_state.jsonl').records();scored={r['payload']['task_id']:r['payload']['verdict']['status'] for r in rows if r['kind']=='PRIVATE_SCORED'}
        maps[arm]={k:v for k,v in scored.items() if v!='INFRASTRUCTURE_MISSING'}
        arms[arm]=dict(completed=len(maps[arm]),infrastructure_missing=sum(v=='INFRASTRUCTURE_MISSING' for v in scored.values()),statuses=dict(collections.Counter(maps[arm].values())))
    common=set.intersection(*(set(m) for m in maps.values()));pairs={}
    for x,y in [('F','G'),('F','T'),('F','R'),('T','G')]:
        a,b=maps[x],maps[y];trusted={k for k in common if a[k] in ('CONFIRMED_CORRECT','CONFIRMED_WRONG') and b[k] in ('CONFIRMED_CORRECT','CONFIRMED_WRONG')}
        pairs[x+'-'+y]=dict(completed_pairs=len(common),x_only_confirmed_correct=sum(a[k]=='CONFIRMED_CORRECT' and b[k]!='CONFIRMED_CORRECT' for k in common),y_only_confirmed_correct=sum(b[k]=='CONFIRMED_CORRECT' and a[k]!='CONFIRMED_CORRECT' for k in common),both_reliably_scored_pairs=len(trusted),trusted_x_wins=sum(a[k]=='CONFIRMED_CORRECT' and b[k]=='CONFIRMED_WRONG' for k in trusted),trusted_y_wins=sum(b[k]=='CONFIRMED_CORRECT' and a[k]=='CONFIRMED_WRONG' for k in trusted))
    settled_upper=unknown_upper=pending_upper=tools_ms=0;unresolved=[]
    for rec in accounts.values():
        s=rec['state'];cost=s.get('settlement',{}).get('cost_microusd',s['cost_upper_microusd'])
        if s['status']=='settled':settled_upper+=cost
        elif s['status']=='unknown':unknown_upper+=cost;unresolved.append(dict(run_id=rec['run_id'],request_id=rec['request_id'],reserved_usd=cost/1e6,status='UNKNOWN'))
        else:pending_upper+=cost;unresolved.append(dict(run_id=rec['run_id'],request_id=rec['request_id'],reserved_usd=cost/1e6,status=s['status']))
        tools_ms+=s.get('settlement',{}).get('tool_milliseconds',s['tool_milliseconds_upper'])
    summary=dict(http_rejections=len(http),unmetered_responses=list(unmetered.values()),arms=arms,paired_results=pairs,unique_model_responses=len(responses),tokens=sum(r['input_tokens']+r['output_tokens'] for r in responses.values()),estimated_peak_usd=sum(r['estimated_peak_usd'] for r in responses.values()),settled_accounts_charged_or_reserved_usd=settled_upper/1e6,unknown_reserved_usd=unknown_upper/1e6,pending_reserved_usd=pending_upper/1e6,total_charged_or_reserved_usd=(settled_upper+unknown_upper+pending_upper)/1e6,actual_invoice='UNAVAILABLE',worker_seconds_accounted=tools_ms/1000,unresolved_requests=unresolved,increment_by_run=increment,notes=['Inherited copied learning costs counted once; parent solver costs included.','Quoted peak estimate is not actual invoice. Settled ledger money may still be a conservative reservation.','Infrastructure missing excluded from completed and paired denominators. UNVERIFIED/TRUNCATED are not mathematics errors.'])
    save(out/'summary.json',summary);save(out/'unique_responses.json',list(responses.values()));save(out/'unique_accounts.json',list(accounts.values()));return summary
