"""Append-only cumulative evidence, uncertain mechanism relations and bounded scheduling.
No model calls, mathematical rules, private scorer values or automatic admission here.
"""
import re,time,copy
from .contracts import canonical,fingerprint
from .evidence import EvidenceStore
from .compile_queue import CompileQueue
VERSION='math-cumulative-evidence-v2-dual-assessment'
from .math_candidate_decision import validate_decision,bind_evidence,generatable
ROLES={'SUPPORT','POSSIBLE','COUNTEREXAMPLE','UNRELATED'}

def exact(v,fields):
    if not isinstance(v,dict) or set(v)!=set(fields):raise ValueError('unexpected or missing fields')

def text(v):
    if not isinstance(v,str) or not v.strip() or len(v)>6000:raise ValueError('bounded nonempty text required')

def excerpt(s,n):
    # Keep both reasoning prefix and final-answer suffix, never masquerade as full output.
    if len(s)<=n:return dict(text=s,is_fragment=False,omission='NONE',sha256=fingerprint(s))
    return dict(text=s[:n//2]+'\n[HOST OMITTED MIDDLE; NOT MODEL TRUNCATION]\n'+s[-n//2:],is_fragment=True,omission='HOST_MIDDLE_OMISSION',sha256=fingerprint(s))

class CumulativeMemory:
    def __init__(self,path,arm,*,paired=False):
        if arm not in ('T','F'):raise ValueError('learning arm')
        self.paired=paired;self.public=EvidenceStore(path/'public.jsonl')
        self.arm=arm;self.raw=EvidenceStore(path/'raw.jsonl');self.views=EvidenceStore(path/'views.jsonl')
        self.clusters=EvidenceStore(path/'clusters.jsonl');self.path=path
    def put(self,store,kind,value,key):
        old=[r['payload'] for r in store.records() if r['kind']==kind and r['payload']['id']==key]
        row=dict(id=key,**value)
        if old:
            if old!=[row]:raise PermissionError('immutable evidence conflict')
        else:store.append(kind,row,time.time())
        return row
    def ingest(self,task,lock,verdict,original,cutoff):
        """Only called by the host after the all-arm scoring barrier; T never stores grades."""
        if lock['sequence']>cutoff or lock['task_id']!=task.task_id:raise PermissionError('future/task mismatch')
        if fingerprint({k:v for k,v in lock.items() if k!='locked_sha256'})!=lock['locked_sha256']:raise PermissionError('lock tampered')
        public=dict(sequence=lock['sequence'],task=task.to_dict(),source_original_id=original,available_after_sequence=lock['sequence'])
        self.put(self.public,'PUBLIC_TASK',public,fingerprint([self.arm,task.task_id,lock['sequence']]))
        if self.arm=='F':
            if verdict.get('status')!='CONFIRMED_WRONG':return None
            if verdict.get('locked_sha256')!=lock['locked_sha256'] or not lock['responses'] or lock['responses'][-1]['finish_reason']!='stop':raise PermissionError('failure must bind complete locked answer')
        value=dict(sequence=lock['sequence'],task=task.to_dict(),source_original_id=original,available_after_sequence=lock['sequence'])
        if self.arm=='F':
            from code_math.private_math_scoring import extract_answer
            value['parsed_wrong_answer']=extract_answer(lock['final_output'])
            value.update(correct=False,final_output=lock['final_output'],locked_sha256=lock['locked_sha256'],
                         trajectory=[{k:r[k] for k in ('text','finish_reason','usage','model')} for r in lock['responses']],
                         delivery_status='COMPLETE',score_binding=dict(status='CONFIRMED_WRONG',locked_sha256=lock['locked_sha256']))
        eid=fingerprint([self.arm,task.task_id,lock['sequence']])
        return self.put(self.raw,'RAW_EVIDENCE',value,eid)
    def facts(self,cutoff):
        rows=(self.public.records() if self.paired else [])+self.raw.records()
        return {r['payload']['id']:r['payload'] for r in rows if r['payload']['available_after_sequence']<=cutoff}
    def state(self,cutoff):
        states={}
        for r in self.clusters.records():
            if r['kind']=='CLUSTER_VERSION' and r['payload']['cutoff']<=cutoff:states[r['payload']['cluster_id']]=r['payload']
        return states
    def retrieved(self,event_ids,cutoff,limit=6):
        """Lexical retrieval is only a shortlist; never asserts a shared mechanism."""
        facts=self.facts(cutoff);states=self.state(cutoff)
        query=set(re.findall(r'\w+', ' '.join(facts[i]['task']['problem'] for i in event_ids).lower()))
        def rank(c):
            words=set(re.findall(r'\w+',canonical(c['hypothesis']).lower()))
            return (-len(query&words)/max(1,len(query|words)),c['cluster_id'])
        ranked=sorted(states.values(),key=rank)
        # Reserve old least-recently-revised candidates to avoid pure keyword lock-in.
        chosen=ranked[:max(0,limit-2)]
        for c in sorted(states.values(),key=lambda c:(c['cutoff'],c['cluster_id']))+ranked:
            if c not in chosen and len(chosen)<limit:chosen.append(c)
        return chosen
    def project(self,fact,chars=1800):
        out=dict(evidence_id=fact['id'],problem=fact['task']['problem'],raw_sha256=fingerprint(fact),available_after_sequence=fact['sequence'])
        if self.arm=='F' and fact.get('correct') is False:out.update(correct=False,parsed_wrong_answer=fact['parsed_wrong_answer'],delivery_status=fact['delivery_status'],final_output=excerpt(fact['final_output'],chars),trajectory=[dict(output=excerpt(r['text'],chars//2),finish_reason=r['finish_reason']) for r in fact['trajectory']])
        return out
    def associate(self,result,visible_ids,allowed_clusters,cutoff,response_sha):
        """Model relations remain UNVERIFIED; no model flag can certify root cause."""
        exact(result,('descriptions','clusters'))
        facts=self.facts(cutoff);visible=set(visible_ids)
        if not visible<=set(facts):raise PermissionError('unknown/future evidence')
        if not isinstance(result['descriptions'],list) or not isinstance(result['clusters'],list) or len(result['clusters'])>3:raise ValueError('bounded relations')
        described=set()
        for d in result['descriptions']:
            exact(d,('evidence_id','task_structure','observable_symptom','possible_cause','possible_correction','uncertainty'))
            if d['evidence_id'] not in visible or d['evidence_id'] in described:raise ValueError('description identity')
            described.add(d['evidence_id'])
            for k,v in d.items():text(v)
        if described!=visible:raise ValueError('describe every supplied event, including unknown mechanisms')
        prepared=[];states=self.state(cutoff)
        for c in result['clusters']:
            exact(c,('cluster_id','hypothesis','assessment','links'))
            exact(c['hypothesis'],('mechanism','uncertainty','applicability','exclusions','input_output'))
            for v in c['hypothesis'].values():text(v)
            bind_evidence(validate_decision(c['assessment']),visible)
            if not isinstance(c['links'],list) or not c['links']:raise ValueError('invalid mechanism')
            cid=c['cluster_id']
            if cid=='NEW':cid=fingerprint([VERSION,response_sha,len(prepared)])
            elif cid not in allowed_clusters or cid not in states:raise PermissionError('cluster not supplied to model')
            links=copy.deepcopy(states.get(cid,{}).get('links',{}));ids=[]
            for link in c['links']:
                exact(link,('evidence_id','relation','reason','evidence_quote','new_information'))
                eid=link['evidence_id']
                if eid not in visible or eid in ids or link['relation'] not in ROLES or type(link['new_information']) is not bool:raise ValueError('link identity/role')
                ids.append(eid);text(link['reason']);text(link['evidence_quote'])
                # Exact quote is evidence of grounding, not proof of the model's inference.
                f=facts[eid];projected=self.project(f);allowed=projected['problem']+'\n'+projected.get('final_output',{}).get('text','')
                if link['evidence_quote'] not in allowed:raise ValueError('ungrounded relation quote')
                links[eid]=dict(link,assessment='MODEL_HYPOTHESIS_UNVERIFIED')
            if cid in [x['cluster_id'] for x in prepared]:raise ValueError('duplicate cluster update')
            state=dict(cluster_id=cid,hypothesis=c['hypothesis'],assessment=c['assessment'],links=links,cutoff=cutoff,
                       response_sha256=response_sha,verified=False)
            state['version']=fingerprint(state);prepared.append(state)
        # All validation precedes writes; keys permit safe completion after host crash.
        for d in result['descriptions']:self.put(self.views,'LEARNING_VIEW',dict(description=d,cutoff=cutoff,response_sha256=response_sha,verified=False),fingerprint([response_sha,d['evidence_id']]))
        for s in prepared:self.put(self.clusters,'CLUSTER_VERSION',s,s['version'])
        return prepared
    def bundle(self,state,cutoff,max_bytes=22000):
        facts=self.facts(cutoff);links=state['links'];eligible=[i for i,l in links.items() if l['relation']!='UNRELATED']
        # Retain counterexamples first, then known-original diversity, then oldest evidence.
        eligible.sort(key=lambda i:(links[i]['relation']!='COUNTEREXAMPLE',facts[i]['source_original_id']=='UNKNOWN',facts[i]['sequence'],i))
        ordered=[];sources=set()
        for i in eligible:
            source=facts[i]['source_original_id'];key=source if source!='UNKNOWN' else facts[i]['task']['task_id']
            if key not in sources or links[i]['relation']=='COUNTEREXAMPLE':ordered.append(i);sources.add(key)
        ordered += [i for i in eligible if i not in ordered]
        history=[r['payload'] for r in self.clusters.records() if r['kind'] in ('VALIDATION_RESULT','SOURCE_DIAGNOSTICS') and r['payload']['cluster_id']==state['cluster_id'] and r['payload']['cutoff']<=cutoff]
        base=dict(version=VERSION,cluster_id=state['cluster_id'],hypothesis_version=state['version'],hypothesis=state['hypothesis'],assessment=state['assessment'],verified=False,evidence=[],omitted=[],validation=history[-3:])
        for i in ordered:
            item=dict(**self.project(facts[i]),relation=links[i]['relation'],relation_reason=links[i]['reason'])
            candidate=copy.deepcopy(base);candidate['evidence'].append(item)
            # Reserve enough room for traceable omitted references.
            if len(canonical(candidate).encode())+len(ordered)*180<=max_bytes:base['evidence'].append(item)
            else:base['omitted'].append(dict(evidence_id=i,raw_sha256=fingerprint(facts[i]),relation=links[i]['relation']))
        # A required counterexample may not silently disappear to make a request sendable.
        if not base['evidence'] or any(x['relation']=='COUNTEREXAMPLE' for x in base['omitted']) or len(canonical(base).encode())>max_bytes:
            raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return base
    def validation(self,cid,job_id,cutoff,result):
        # Host path only. Gate results never enter this public diagnosis projection.
        status=result['status'];allowed=('STATIC_OR_INTERFACE_REJECTED','DELIVERY_REJECTED','REVISION_DELIVERY_REJECTED','SETTLED_DELIVERY_REJECTED')
        payload=dict(cluster_id=cid,job_id=job_id,cutoff=cutoff,status=status if status in allowed or status in ('NO_MECHANISM','HYPOTHESIS_ONLY','NEEDS_SPECIFICATION','NOT_GENERATABLE') else 'ARTIFACT_SAVED_REVIEW_NOT_PROJECTED',verified=False)
        self.put(self.clusters,'VALIDATION_RESULT',payload,job_id)

class CumulativeQueue(CompileQueue):
    """Reuse queue journal; no periodic expiration or count-only generation threshold."""
    def schedule(self,memory,cutoff,*,budget_available,max_jobs=1,interface_version='semantic-contract-v1'):
        previous=[r['payload'] for r in self.events.records() if r['kind']=='CUMULATIVE_JOB_STARTED']
        active={r['payload']['job_id'] for r in self.events.records() if r['kind']=='CUMULATIVE_JOB_FINISHED'}
        if any(j['job_id'] not in active for j in previous):raise RuntimeError('unfinished cumulative job; replay receipt before new scheduling')
        facts=memory.facts(cutoff);ranked=[]
        for c in memory.state(cutoff).values():
            links={i:l for i,l in c['links'].items() if l['relation']!='UNRELATED'}
            prior=[j for j in previous if j['cluster_id']==c['cluster_id']];used={i for j in prior for i in j['evidence_ids']}
            fresh=set(links)-used;known={facts[i]['source_original_id'] for i in links if facts[i]['source_original_id']!='UNKNOWN'}
            old_known={facts[i]['source_original_id'] for i in used if facts[i]['source_original_id']!='UNKNOWN'}
            material=[i for i in fresh if links[i]['relation']=='COUNTEREXAMPLE' or links[i]['new_information'] or facts[i]['source_original_id'] not in old_known and facts[i]['source_original_id']!='UNKNOWN']
            reason='NO_NEW_INFORMATION' if not fresh or (prior and not material) else c['assessment']['algorithm_candidate']['decision'] if not generatable(c['assessment']) else 'NO_BUDGET' if not budget_available else ''
            job=dict(cluster_id=c['cluster_id'],hypothesis_version=c['version'],evidence_ids=sorted(links),new_evidence_ids=sorted(fresh),interface_version=interface_version,
                     decision='REVISE_HYPOTHESIS_AND_GENERATE' if prior else 'EXPLORE_SINGLE_WITNESS' if len(known)<2 else 'GENERATE',
                     priority_basis=dict(new_counterexamples=sum(links[i]['relation']=='COUNTEREXAMPLE' for i in fresh),new_confirmed_originals=len(known-old_known),confirmed_originals=len(known),prior_attempts=len(prior),material_evidence_ids=material,root_cause_verified=False))
            job['job_id']=fingerprint([VERSION,c['cluster_id'],sorted(links),c['version'],interface_version]);rank=(-job['priority_basis']['new_counterexamples'],-len(known-old_known),len(prior),c['cluster_id'])
            ranked.append((rank,job,reason))
        selected=[]
        for _,job,reason in sorted(ranked):
            if not reason and len(selected)>=max_jobs:reason='BOUNDARY_JOB_LIMIT'
            self.events.append('CUMULATIVE_SCHEDULE',dict(job,cutoff=cutoff,skip_reason=reason),time.time())
            if not reason:selected.append(job)
        return selected
    def start(self,job):
        if any(r['kind']=='CUMULATIVE_JOB_STARTED' and r['payload']['job_id']==job['job_id'] for r in self.events.records()):raise RuntimeError('consumed job')
        self.events.append('CUMULATIVE_JOB_STARTED',job,time.time())
    def finish(self,job,result):
        if not any(r['kind']=='CUMULATIVE_JOB_FINISHED' and r['payload']['job_id']==job['job_id'] for r in self.events.records()):self.events.append('CUMULATIVE_JOB_FINISHED',dict(job_id=job['job_id'],result=result),time.time())
