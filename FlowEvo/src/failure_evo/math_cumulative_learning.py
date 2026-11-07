"""Model-connected cumulative learner. Existing compiler, transport, Gate and Worker.
Relation proposals are uncertain knowledge, not permission or validated mathematics.
"""
import json,time,copy
from pathlib import Path
from .contracts import canonical,fingerprint
from .math_cumulative import CumulativeMemory,CumulativeQueue,exact,VERSION
from .math_stream import budget,save,read
from .math_stream_learning import WindowLearner,StreamCompilerAdapter,ReviewedRelease,diagnosis
from .math_candidate_decision import SCHEMA,INSTRUCTIONS,validate_decision,bind_evidence,generatable
from .math_v3_component_generation import SAFETY
from .semantic_contract import FIELDS
from .math_engineering_repair import receive_source,version_change
from .semantic_contract import artifact
from .compile_queue import BoundedCompiler
from .run_health import RunUnhealthy
from .evidence_links import INSTRUCTIONS as LINK_INSTRUCTIONS,LinkConflict,validate_revision
from .cluster_contract import ClusterContext,ClusterProposal,reject_permissions,BOUNDARY_INSTRUCTIONS

RELATION_EXAMPLE=dict(descriptions=[dict(evidence_id='supplied ID',task_structure='observed structure',observable_symptom='observation or UNKNOWN',possible_cause='unverified hypothesis or UNKNOWN',possible_correction='unverified proposal or UNKNOWN',uncertainty='limits')],clusters=[dict(cluster_id='NEW or supplied cluster ID',hypothesis=dict(mechanism='unverified computation',uncertainty='limits',applicability='premises',exclusions='boundaries',input_output='parameterized interface'),assessment=dict(mechanism_assessment=dict(status='SUSPECTED',reason='uncertain',evidence_refs=[]),algorithm_candidate=dict(decision='NEEDS_SPECIFICATION',reason='concrete computation not established',details=None)),links=[dict(evidence_id='supplied ID',relation='SUPPORTS/CONTRADICTS/UNRELATED/UNCERTAIN',reason='specific relationship',quote_spans=['exact supplied quote'],new_information=False)])])
def parse_relations(v):
    reject_permissions(v)
    exact(v,('descriptions','clusters'))
    if not isinstance(v['descriptions'],list) or not isinstance(v['clusters'],list):raise ValueError('relation arrays')
    for c in v['clusters']:ClusterProposal.validate(c)
    return v
class AssociationAdapter(StreamCompilerAdapter):
    protocol=VERSION;hypothesis_parser=staticmethod(parse_relations)
    def preflight(self,r):
        self._authorize();bundle=r['association_input']
        if set(bundle) not in ({'version','evidence','candidate_clusters','selection'},{'version','evidence','candidate_clusters','selection','relation_revision'}) or bundle['version']!=VERSION:raise PermissionError('association whitelist')
        for context in bundle['candidate_clusters']:ClusterContext.validate(context)
        # Host constructs this projection; no private row, task-ID-based answer or future task is accepted.
        system=(BOUNDARY_INSTRUCTIONS+LINK_INSTRUCTIONS+'Describe the supplied historical public evidence, separating observations from uncertain causes and proposed corrections. '
                'Do not equate a subject label or wrong answer with a common mechanism. Retrieve candidate relationships using task structure, reasoning, observed symptoms and possible corrections. '
                'A record may belong to multiple hypotheses or none. State UNKNOWN when unsupported. Candidate clusters and their claims are UNVERIFIED. '
                'Host text omissions are not model truncation; finish_reason describes actual delivery. Do not infer correctness from absent feedback. '
                'No fixed algorithm, mechanism name, number, success or root cause is required. Do not invent quotes. Do not certify truth or permissions. '
                'Return JSON with exactly the example keys; clusters may be empty; descriptions must cover all supplied evidence. Relation must follow evidence-link-v2. '
                +INSTRUCTIONS.replace('Return the exact JSON schema: ','Each cluster assessment must conform to this schema: ')+canonical(SCHEMA)+' new_information says whether this record challenges or materially extends the mechanism rather than repeats a symptom. Schema example: '+canonical(RELATION_EXAMPLE))
        wire=dict(model=self.model,messages=[dict(role='system',content=system),dict(role='user',content=canonical(bundle))],max_tokens=r['max_tokens'],temperature=0,thinking={'type':'disabled'},reasoning_effort='none',response_format={'type':'json_object'},stream=False)
        if len(canonical(wire).encode())+256>self.max_wire_input_upper:raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return wire
# A concrete JSON serialization example, not a valid candidate contract.
DELIVERY_EXAMPLE=json.dumps(dict(
    description=canonical(dict(example='semantic contract fields go here')),
    applicability=canonical(dict(example='Operator Contract fields go here')),
    code="def example():\n    return 'text'\n"))


def settled_malformed_json(response):
    """Only a received, metered, stopped response with invalid outer JSON may be replaced."""
    from .run_health import trusted_usage

    if (response.get('transport_status')!='RESPONSE_RECEIVED'
            or response.get('parse_status')!='COMPILE_OUTPUT_CONTRACT_ERROR'
            or response.get('finish_reason')!='stop'):
        return False
    raw=response.get('raw_response')
    if not isinstance(raw,dict) or fingerprint(raw)!=response.get('response_sha256') or not trusted_usage(raw):
        return False
    choices=raw.get('choices',[])
    if len(choices)!=1 or choices[0].get('finish_reason')!='stop':
        return False
    content=choices[0].get('message',{}).get('content')
    if not isinstance(content,str) or not content.strip():
        return False
    try:
        json.loads(content)
    except json.JSONDecodeError:
        return True
    return False


def request_candidate_delivery(request, job):
    response=request('candidate',0)
    if not settled_malformed_json(response):
        return response,False
    job['delivery_repair']=dict(reason='MALFORMED_OUTER_JSON',
                                parent_response_sha256=response['response_sha256'])
    return request('candidate',1),True


class BundleCompilerAdapter(StreamCompilerAdapter):
    protocol=VERSION;hypothesis_parser=staticmethod(validate_decision)
    def preflight(self,r):
        self._authorize();packet=r['public_evidence'];arm=r['arm']
        if arm not in ('T','F') or set(packet)!=({'questions','observations'} if arm=='F' else {'questions'}):raise PermissionError('public evidence fields')
        for q in packet['questions']:
            if set(q)!={'problem'}:raise PermissionError('public question fields')
        for o in packet.get('observations',[]):
            if set(o)!={'problem','correct','final_output','trajectory'} or o['correct'] is not False or o['problem'] not in [q['problem'] for q in packet['questions']]:raise PermissionError('public observation fields')
            if set(o['final_output'])!={'text','is_fragment','sha256'} or any(set(t)!={'text','is_fragment','sha256','finish_reason'} for t in o['trajectory']):raise PermissionError('trajectory fields')
        data=dict(evidence=packet,learning_evidence_bundle=r['learning_evidence_bundle'])
        if r['phase']=='induction':system=INSTRUCTIONS+canonical(SCHEMA)
        else:
            assessment=bind_evidence(validate_decision(json.loads(r['specification'])),[x['evidence_id'] for x in r['learning_evidence_bundle']['evidence']])
            if not generatable(assessment):raise PermissionError('candidate not ready for generation')
            data['hypothesis']=assessment
            system=(SAFETY+' Implement the candidate computation, not the suspected failure operation. Cause confidence is not correctness. '
                    'Source must define solve(parameters), returning a nonempty numerical string, and match(problem). '
                    'match returns exactly status (MATCH/DECLINE/UNKNOWN), parameters (object), reason (string), assumption_quotes (list of exact public substrings), requested_quantity (string). '
                    'Match only supported objectives and confirmed premises; otherwise decline. No self-tests or math_operator entry. '
                    'description must be a JSON-encoded contract with exactly nonempty string fields '+','.join(FIELDS)+'. '
                    'parameter_schema is a closed object schema without references; requested_quantity equals match requested_quantity. '
                    'DIAGNOSTIC outputs are diagnostic numerical results, never final answers to a different mathematical objective. '
                    'applicability must be a JSON-encoded Operator Contract object with exactly artifact_kind, input_schema, preconditions, output_schema, algorithm, complexity_bound, failure_modes, source_evidence. '
                    'artifact_kind is INSTANCE_SOLVER or REUSABLE_CANDIDATE, not a validation claim. input_schema, output_schema, complexity_bound are nonempty objects; preconditions, failure_modes, source_evidence are nonempty string lists. algorithm is a nonempty string. '
                    'source_evidence must equal the supplied evidence IDs. Never output validation_status, verified, gate_passed, execution_authorized. '
                    'Return exactly one JSON object with three nonempty string values: description, applicability, code. '
                    'Put the two metadata values before code. Escape quotes, backslashes and line breaks as JSON. '
                    'Keep code concise. The code string contains only Python defining the required functions. '
                    'Do not define description or applicability inside Python, add a result envelope, or return a dictionary containing the source. '
                    'Close the code string and the outer object. No Markdown. Do not assert validation or permissions. '
                    'Serialization example only; use the actual contract fields and implement your own computation: '+DELIVERY_EXAMPLE)
            if r.get('delivery_repair'):
                if r['phase']!='candidate' or r['slot']!=1:
                    raise PermissionError('delivery repair uses one distinct candidate slot')
                system+=' The previous outer JSON was invalid. Deliver a fresh complete candidate from the same frozen specification. '
            if r['phase']=='revision':
                data.update(previous_source=r['code'],engineering_diagnostics=r['engineering_diagnostics'])
                system+=' Repair the stated engineering problems; disclose any computational logic changes. No reference answers are provided.'
        wire=dict(model=self.model,messages=[dict(role='system',content=system),dict(role='user',content=canonical(data))],max_tokens=r['max_tokens'],temperature=0,thinking={'type':'disabled'},reasoning_effort='none',response_format={'type':'json_object'},stream=False)
        if len(canonical(wire).encode())+256>self.max_wire_input_upper:raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return wire

class CumulativeLearner(WindowLearner):
    def __init__(self,stream,arm,*,sender=None,release=None,budget_factory=None):
        self.budget_factory=budget_factory
        super().__init__(stream,arm,sender=sender,release=release)
        self.cfg=stream.plan['cumulative'];self.root=stream.arms[arm]['path']/'cumulative'
        self.memory=CumulativeMemory(self.root,arm,paired=self.cfg['comparison']=='paired_information')
        self.queue=CumulativeQueue(self.root/'queue.jsonl')
    def ingest(self,task,lock,verdict,seq):
        self.memory.ingest(task,lock,verdict,self.stream.lineage[task.task_id].get('source_original_id','UNKNOWN'),seq)
    def _path(self,cutoff,key):
        # All auxiliary ledgers stay under reporting windows, so existing R lagged call credit counts them.
        end=((cutoff-1)//self.stream.plan['window']+1)*self.stream.plan['window']
        return self.stream.arms[self.arm]['path']/'learning'/str(end)/'jobs'/key
    def capacity(self,cutoff,calls,*,gate=False):
        from .persistent_budget import PersistentBudget
        window=self._path(cutoff,'placeholder').parent;allocated=0;learning=0
        for p in window.rglob('*budget.jsonl'):
            b=PersistentBudget.__new__(PersistentBudget);b.path=p
            with b._locked() as rows:
                n=rows[0]['payload']['config']['max_calls'];allocated+=n
                if p.name=='generation_budget.jsonl':learning+=n
        return allocated+calls<=self.stream.plan['r_max_extra_calls'] and (gate or learning+calls<=self.stream.plan.get('learning_calls_per_window',self.stream.plan['r_max_extra_calls']))
    def _authorize(self):
        if not self.stream.engineering:
            auth=getattr(self,'paid_authorization',{})
            if not self.cfg.get('paid_api_authorized',False) and not (auth.get('paid_api_authorized') is True and auth.get('run_id')==self.stream.path.name and auth.get('protocol_sha256')==self.stream.ph):raise PermissionError('cumulative learning paid authorization absent')
    def _provider(self,path,cls,calls):
        self._authorize();s=self.stream
        b=(self.budget_factory(path/'generation_budget.jsonl',calls) if self.budget_factory
           else budget(path/'generation_budget.jsonl',('engineering:' if s.engineering else '')+s.path.name+':'+self.arm+':cumulative:'+path.name,s.ph,calls=calls))
        auth=dict(run_id=b.config['run_id'],protocol_hash=s.ph,model='deepseek-flash',protocol=VERSION,max_cost_microusd=b.config['max_cost_microusd'],paid_api_authorized=True)
        provider=cls(path/'provider.jsonl',b,model='deepseek-flash',authorization=auth,mock=s.engineering,sender=self.sender,max_wire_input_upper=self.cfg['wire_upper'],network_policy=s.plan.get('network_policy'))
        return b,provider,BoundedCompiler(provider,b,path/'compiler.jsonl','deepseek-flash',max_input_upper=self.cfg['wire_upper'],max_output_upper=self.cfg['output_upper'])
    def discover(self,cutoff):
        s=self.stream;facts=self.memory.facts(cutoff)
        previous=[r['payload'] for r in self.memory.views.records() if r['kind']=='ASSOCIATION_DONE']
        consumed={i for p in previous for i in p['evidence_ids']}
        if self.cfg['comparison']=='paired_information':
            packs=[x for x in self.cfg['paired_packs'] if x['after_sequence']==cutoff]
            if not packs:return
            ids=[i for i,f in facts.items() if f['task']['task_id'] in packs[0]['task_ids']]
            if len(ids)!=len(packs[0]['task_ids']):raise PermissionError('paired public packet incomplete')
        else:
            from .evidence_retrieval import select
            retrieval=select(self.memory,cutoff,max_records=self.cfg['association_batch'],max_bytes=self.cfg['bundle_bytes'])
            ids=retrieval['selected_ids']
            from .evidence import EvidenceStore
            self.memory.put(EvidenceStore(self.root/'retrieval.jsonl'),'EVIDENCE_RETRIEVAL',retrieval,fingerprint(retrieval))
        if not ids or set(ids)<=consumed:return
        if len(previous)>=self.cfg['max_association_jobs']:return
        key=fingerprint(['associate-lifecycle-v1',self.arm,ids]);path=self._path(cutoff,key)
        # Recovery reuses its already allocated account; it is not a new job.
        if not (path/'generation_budget.jsonl').exists() and not self.capacity(cutoff,1):return
        path.mkdir(parents=True,exist_ok=True)
        chosen=self.memory.retrieved(ids,cutoff,self.cfg['retrieval_limit']) if self.cfg['comparison']=='workflow' else []
        visible_ids=list(ids)
        for c in chosen:
            linked=[i for i,l in c['links'].items() if l['relation']!='UNRELATED' and i in facts]
            counter=[i for i in linked if c['links'][i]['relation']=='COUNTEREXAMPLE']
            representative=sorted(linked,key=lambda i:(facts[i]['sequence'],i))[:1]
            for i in counter+representative:
                if i not in visible_ids:visible_ids.append(i)
        if self.cfg['comparison']=='workflow':
            # Independent evidence shortlist owns the total evidence cap. Cluster
            # context is optional; omit whole clusters whose witnesses do not fit.
            visible_ids=list(ids);kept=[]
            for c in chosen:
                linked=[i for i,l in c['links'].items() if l['relation']!='UNRELATED' and i in facts]
                needed=[i for i in linked if c['links'][i]['relation']=='COUNTEREXAMPLE']
                needed+=sorted(linked,key=lambda i:(facts[i]['sequence'],i))[:1]
                trial=list(dict.fromkeys(visible_ids+needed))
                if len(trial)<=self.cfg['association_batch'] and len(canonical([self.memory.project(facts[i]) for i in trial]).encode())<=self.cfg['bundle_bytes']:
                    visible_ids=trial;kept.append(c)
            chosen=kept
        allowed=[c['cluster_id'] for c in chosen]
        payload=dict(version=VERSION,evidence=[self.memory.project(facts[i]) for i in visible_ids],candidate_clusters=[ClusterContext.from_host(c).to_dict() for c in chosen],selection=self.cfg['comparison'])
        # Input immutable across restart; old clusters cannot replace those originally supplied.
        frozen=dict(payload=payload,ids=ids,visible_ids=visible_ids,allowed=allowed,cutoff=cutoff)
        if (path/'input.json').exists():frozen=read(path/'input.json');payload=frozen['payload'];allowed=frozen['allowed'];visible_ids=frozen['visible_ids']
        else:save(path/'input.json',frozen)
        b,provider,compiler=self._provider(path,AssociationAdapter,1)
        job=dict(stream_id=b.config['run_id'],family_id=key,association_input=payload,arm=self.arm)
        responses=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_COMPLETED']
        try:
            if responses:result=json.loads(responses[-1]['content'])
            else:
                prior=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_REQUESTED']
                if prior and not (len(prior)==1 and provider.can_resume_pre_send(prior[0])):raise RunUnhealthy('association incomplete; no resend')
                response=compiler.request(job,'induction',0,time.time(),output_upper=self.cfg['output_upper']);result=json.loads(response['specification'])
            response_sha=fingerprint(result)
            if self.cfg['comparison']=='paired_information' and len(result['clusters'])>1:raise ValueError('paired protocol allows one hypothesis per frozen pack')
            self.memory.associate(result,visible_ids,allowed,cutoff,response_sha)
            outcome='ACCEPTED_UNVERIFIED'
        except LinkConflict as exc:
            s.health()
            outcome=self.repair_relation_conflict(path,job,result,exc.diagnostic,visible_ids,allowed,cutoff)
        except ValueError as exc:
            s.health();outcome='REJECTED:'+str(exc)
        receipts=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_RESPONSE']
        requests=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_REQUESTED']
        self.memory.put(self.memory.attempts,'ASSOCIATION_ATTEMPT',dict(
            evidence_ids=visible_ids,selected_ids=ids,cutoff=cutoff,schema_version=VERSION,
            policy_version='association-lifecycle-v1',
            request_id=fingerprint(['generation',(job['stream_id'],job['family_id']),'induction',0]),
            request_sha256=fingerprint(requests[0]) if requests else None,
            parse_status=receipts[-1]['response'].get('delivery_status','UNKNOWN') if receipts else 'UNKNOWN',
            rejection_reason=outcome if outcome.startswith('REJECTED:') else None,
            raw_response_sha256=fingerprint(receipts[-1]['response'].get('raw_response')) if receipts else None,
            outcome=outcome,budget=b.snapshot(),provider_path=str(path/'provider.jsonl')),key)
        self.memory.put(self.memory.views,'ASSOCIATION_DONE',dict(evidence_ids=ids,cutoff=cutoff,outcome=outcome,path=str(path)),key)
    def repair_relation_conflict(self,parent,job,proposal,diagnostic,visible_ids,allowed,cutoff):
        # One distinct paid revision at most. No reset/retry of unknown requests.
        path=parent/'relation_revision'
        if (path/'result.json').exists():return read(path/'result.json')['outcome']
        if not (path/'generation_budget.jsonl').exists() and not self.capacity(cutoff,1):
            return 'REJECTED:RELATION_REVISION_NO_BUDGET'
        path.mkdir(parents=True,exist_ok=True)
        data=copy.deepcopy(job['association_input'])
        data['relation_revision']=dict(previous_proposal=proposal,diagnostic=diagnostic,
            instruction='Revise only relation representation and aggregate judgment. Preserve evidence; no new IDs or permissions. One attempt only.')
        frozen=dict(payload=data,visible_ids=visible_ids,allowed=allowed,cutoff=cutoff)
        if (path/'input.json').exists():
            if read(path/'input.json')!=frozen:raise RunUnhealthy('relation revision input drift')
        else:save(path/'input.json',frozen)
        b,provider,compiler=self._provider(path,AssociationAdapter,1)
        revised_job=dict(stream_id=b.config['run_id'],family_id=fingerprint([job['family_id'],'relation-revision-v1']),association_input=data,arm=self.arm)
        completed=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_COMPLETED']
        try:
            if completed:value=json.loads(completed[-1]['content'])
            else:
                prior=[r['payload'] for r in compiler.events.records() if r['kind']=='GENERATION_REQUESTED']
                if prior and not (len(prior)==1 and provider.can_resume_pre_send(prior[0])):raise RunUnhealthy('relation revision consumed; no resend')
                response=compiler.request(revised_job,'induction',0,time.time(),output_upper=self.cfg['output_upper'])
                value=json.loads(response['specification'])
            validate_revision(proposal,value)
            if self.cfg['comparison']=='paired_information' and len(value['clusters'])>1:raise ValueError('paired cluster count')
            self.memory.associate(value,visible_ids,allowed,cutoff,fingerprint(value))
            outcome='ACCEPTED_UNVERIFIED_AFTER_RELATION_REVISION'
        except ValueError as exc:
            self.stream.health();outcome='REJECTED:RELATION_REVISION:'+str(exc)
        save(path/'result.json',dict(outcome=outcome,diagnostic=diagnostic,original_proposal_sha256=fingerprint(proposal),budget=b.snapshot(),max_revisions=1))
        return outcome
    def boundary(self,cutoff):
        s=self.stream;s.health()
        for a in s.arms.values():
            if not any(r['kind']=='PRIVATE_SCORED' and r['payload']['sequence']==cutoff for r in a['states'].records()):raise PermissionError('learning before all-arm lock/score barrier')
        # No work at terminal task: there are no future tasks to benefit.
        if cutoff==len(s.tasks):return
        self.learn_visible_prefix(cutoff)

    def learn_visible_prefix(self,cutoff):
        if hasattr(self.release,'poll'):self.release.poll(cutoff)
        self.discover(cutoff)
        # Complete durable prior outcomes before scheduling any new job.
        done={r['payload']['job_id'] for r in self.queue.events.records() if r['kind']=='CUMULATIVE_JOB_FINISHED'}
        started=[r['payload'] for r in self.queue.events.records() if r['kind']=='CUMULATIVE_JOB_STARTED']
        for j in started:
            if j['job_id'] not in done:
                result=self.execute(j,j['cutoff']);self.memory.validation(j['cluster_id'],j['job_id'],j['cutoff'],result);self.queue.finish(j,result)
        jobs=self.queue.schedule(self.memory,cutoff,budget_available=len(started)<self.cfg['max_generation_jobs'] and self.capacity(cutoff,3),max_jobs=1)
        for j in jobs:
            j['cutoff']=cutoff
            try:bundle=self.memory.bundle(self.memory.state(cutoff)[j['cluster_id']],cutoff,self.cfg['bundle_bytes'])
            except ValueError as e:
                self.queue.events.append('CUMULATIVE_BUNDLE_BLOCKED',dict(job_id=j['job_id'],cutoff=cutoff,reason=str(e)),time.time());continue
            if self.cfg['comparison']=='paired_information':
                pack=next((p for p in self.cfg['paired_packs'] if p['after_sequence']==cutoff),None)
                if pack is None:continue
                facts=self.memory.facts(cutoff)
                ids=[i for tid in pack['task_ids'] for i,f in facts.items() if f['task']['task_id']==tid]
                bundle['evidence']=[dict(**self.memory.project(facts[i]),relation='PAIRED_PUBLIC_TASK',relation_reason='Frozen before outcomes; no failure-based selection') for i in ids]
                bundle['omitted']=[]
                if len(canonical(bundle).encode())>self.cfg['bundle_bytes']:raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
            bundle['selection']=self.cfg['comparison'];bundle['new_evidence_ids']=j['new_evidence_ids'];j['bundle']=bundle
            self.queue.start(j);result=self.execute(j,cutoff)
            self.memory.validation(j['cluster_id'],j['job_id'],cutoff,result);self.queue.finish(j,result)
    def learn(self,cutoff):
        # Reporting only: no evidence expires at this window boundary.
        path=self.stream.arms[self.arm]['path']/'learning'/str(cutoff);calls=0
        from .persistent_budget import PersistentBudget
        for p in path.rglob('*budget.jsonl'):
            b=PersistentBudget.__new__(PersistentBudget);b.path=p
            with b._locked() as rows:states,_=b._state(rows);calls+=sum(x['kind']=='model' and x['status']!='not_sent' for x in states.values())
        save(path/'result.json',dict(status='CUMULATIVE_WINDOW_ACCOUNTED',learning_calls=calls,cutoff=cutoff))
    def execute(self,j,cutoff):
        s=self.stream;a=s.arms[self.arm];path=self._path(cutoff,j['job_id']);path.mkdir(parents=True,exist_ok=True)
        if (path/'result.json').exists():return read(path/'result.json')
        bundle=j['bundle'];facts=self.memory.facts(cutoff);ids=[x['evidence_id'] for x in bundle['evidence']]
        packet=dict(questions=[dict(problem=facts[i]['task']['problem']) for i in ids])
        if self.arm=='F':
            packet['observations']=[dict(problem=facts[i]['task']['problem'],correct=False,
                final_output={k:v for k,v in self.memory.project(facts[i])['final_output'].items() if k in ('text','is_fragment','sha256')},
                trajectory=[dict(text=t['output']['text'],is_fragment=t['output']['is_fragment'],sha256=t['output']['sha256'],finish_reason=t['finish_reason']) for t in self.memory.project(facts[i])['trajectory']]) for i in ids if facts[i].get('correct') is False]
        refs=dict(task_ids=[facts[i]['task']['task_id'] for i in ids],omitted_task_ids=[],cutoff_sequence=cutoff)
        s.emit_once(a['registry'].events,'STREAM_LEARNING_INPUT',j['job_id'],refs)
        save(path/'public_input.json',packet);save(path/'bundle.json',bundle)
        def finish(result):
            save(path/'result.json',dict(cutoff=cutoff,arm=self.arm,**result));return read(path/'result.json')
        b,provider,compiler=self._provider(path,BundleCompilerAdapter,3)
        job=dict(stream_id=b.config['run_id'],family_id=j['job_id'],arm=self.arm,public_evidence=packet,prior_hypotheses=[],learning_evidence_bundle=bundle)
        def request(phase,slot=0):
            rows=compiler.events.records()
            requests=[r['payload'] for r in rows if r['kind']=='GENERATION_REQUESTED'
                      and r['payload']['phase']==phase and r['payload']['slot']==slot]
            if requests:
                request_hash=fingerprint(requests[0])
                responses=[r['payload']['response'] for r in rows if r['kind']=='GENERATION_RESPONSE'
                           and r['payload']['request_sha256']==request_hash]
                complete=[r for r in rows if r['kind']=='GENERATION_COMPLETED'
                          and r['payload']['request_sha256']==request_hash]
                if responses and complete:return responses[-1]
                if phase=='candidate' and len(responses)==1 and settled_malformed_json(responses[0]):
                    s.health()
                    return responses[0]
                if not (len(requests)==1 and provider.can_resume_pre_send(requests[0])):
                    raise RunUnhealthy('incomplete generation; no resend')
            try:
                return compiler.request(job,phase,slot,time.time(),output_upper=self.cfg['output_upper'])
            except ValueError as exc:
                if phase!='candidate' or str(exc)!='COMPILE_OUTPUT_CONTRACT_ERROR':
                    raise
                receipts=compiler.events.records()
                latest=receipts[-1]
                if latest['kind']!='GENERATION_RESPONSE' or not settled_malformed_json(latest['payload']['response']):
                    raise
                s.health()
                return latest['payload']['response']
        try:
            r=request('induction');hyp=bind_evidence(validate_decision(json.loads(r['specification'])),ids)
            s.emit_once(a['registry'].events,'STREAM_HYPOTHESIS',j['job_id'],dict(hypothesis=hyp,task_ids=refs['task_ids'],cutoff=cutoff))
            save(path/'hypothesis.json',hyp)
            if not generatable(hyp):return finish(dict(status=hyp['algorithm_candidate']['decision'],mechanism_assessment=hyp['mechanism_assessment'],learning_calls=b.snapshot()['calls']))
            job['specification']=r['specification']
            response,replaced=request_candidate_delivery(request,job)
            rejection=receive_source(response,'MOCK' if s.engineering else 'DEEPSEEK')
            if rejection:return finish(dict(status='DELIVERY_REJECTED',reason=rejection,
                delivery_replacement=replaced,learning_calls=b.snapshot()['calls']))
            save(path/'original_response.json',response);(path/'original.py').write_text(response['code'])
            diag,contract=diagnosis(response);save(path/'engineering_diagnosis.json',diag)
            if not diag['passed'] and not replaced:
                job.update(code=response['code'],engineering_diagnostics=diag)
                revised=request('revision');rejection=receive_source(revised,'MOCK' if s.engineering else 'DEEPSEEK')
                save(path/'revision_response.json',revised)
                if rejection:return finish(dict(status='REVISION_DELIVERY_REJECTED',reason=rejection,learning_calls=b.snapshot()['calls']))
                save(path/'version_change.json',version_change(response['code'],revised['code']));response=revised;diag,contract=diagnosis(response)
                save(path/'revised_diagnosis.json',diag)
            if not diag['passed']:return finish(dict(status='STATIC_OR_INTERFACE_REJECTED',diagnosis=diag,learning_calls=b.snapshot()['calls']))
            # Exactly the generated source is used in both component paths; no host-written algorithm.
            used=sorted({t for rr in a['registry'].events.records() if rr['kind']=='STREAM_LEARNING_INPUT' for t in rr['payload']['task_ids']})
            art=artifact(path/'artifact',response['code'],response['code'],contract,provenance=dict(origin='MOCK' if s.engineering else 'DEEPSEEK',response_sha256=response['response_sha256'],request_sha256=response['wire_sha256'],excluded_task_ids=used,assessment_sha256=fingerprint(hyp),output_role=hyp['algorithm_candidate']['details']['output']['role']))
            from .operator_contract import attach_contract
            try:
                art=attach_contract(art,json.loads(response['applicability']),evidence_ids=ids,protocol=provider.protocol,
                    original_ids=sorted({facts[i].get('source_original_id','UNKNOWN') for i in ids}))
            except (ValueError,TypeError) as exc:
                save(path/'operator_contract_rejection.json',dict(status='CONTRACT_REJECTED',reason=str(exc),response_sha256=response['response_sha256']))
                return finish(dict(status='OPERATOR_CONTRACT_REJECTED',reason=str(exc),learning_calls=b.snapshot()['calls']))
            art['candidate_created_after']=cutoff
            art['learning_provenance']=dict(candidate_generation_job_id=j['job_id'],cluster_id=j['cluster_id'],cluster_version=j['hypothesis_version'],
                source_evidence_ids=ids,association_attempt_ids=[r['payload']['id'] for r in self.memory.attempts.records() if r['payload']['cutoff']<=cutoff and set(r['payload']['evidence_ids']) & set(ids)],
                mechanism_assessment=hyp['mechanism_assessment'],algorithm_candidate=hyp['algorithm_candidate'],hypothesis_sha256=fingerprint(hyp),
                delivery_repair=job.get('delivery_repair'))
            save(path/'artifact.json',art)
            if not any(rr['kind']=='MATH_SHADOW' and rr['payload']==art for rr in a['registry'].events.records()):a['registry'].shadow(art)
            from .math_contract_runtime import validate_safety
            safety=validate_safety(a['registry'],art,a['split'],engineering=s.engineering)
            if not safety['passed']:return finish(dict(status='SHADOW_STATIC_SAFETY_REJECTED',learning_calls=b.snapshot()['calls']))
            # Diagnostics are bound to publicly available source tasks, no gold enters Worker.
            source=[];byid={t.task_id:t for t in s.tasks}
            if (path/'VALIDATION_STARTED.json').exists():raise RunUnhealthy('interrupted validation requires audit; no implicit Worker replay')
            save(path/'VALIDATION_STARTED.json',dict(code_sha256=art['code_sha256'],cutoff=cutoff))
            for tid in refs['task_ids']:
                t=byid[tid];result=a['split'].run(art,t)
                source.append(dict(task_id=tid,execution=result,combined_source=s.source_review(self.arm,t,result,cutoff) if hyp['algorithm_candidate']['details']['output']['role']=='ANSWER' else dict(status='DIAGNOSTIC_NOT_ANSWER_SCORED',correct=None),parameter_correctness='UNVERIFIED_NO_INDEPENDENT_PARAMETER_REVIEW',computation_correctness='UNVERIFIED',status='EXECUTED_UNVERIFIED'))
            save(path/'source_execution.json',source)
            self.memory.put(self.memory.clusters,'SOURCE_DIAGNOSTICS',dict(cluster_id=j['cluster_id'],cutoff=cutoff,
                artifact_sha256=art['code_sha256'],checks=[dict(task_id=x['task_id'],status=x['combined_source']['status'],correct=x['combined_source'].get('correct'),
                parameter_correctness=x['parameter_correctness'],computation_correctness=x['computation_correctness']) for x in source],
                note='Host source-only post-lock checks; not independent Gate or shared-cause proof'),j['job_id'])
            released=self.release.attempt(art,cutoff,path) if hyp['algorithm_candidate']['details']['output']['role']=='ANSWER' else dict(status='SHADOW_DIAGNOSTIC_ONLY',gate_passed=False)
            return finish(dict(**released,artifact=art,learning_calls=b.snapshot()['calls'],source_executions=len(source)))
        except ValueError as exc:
            s.health()
            # Settled delivery failures are research outcomes, never fabricated UNKNOWN requests.
            if str(exc).startswith('COMPILE_OUTPUT_') or str(exc)=='compiler returned no specification/artifact':
                return finish(dict(status='SETTLED_DELIVERY_REJECTED',reason=str(exc),learning_calls=b.snapshot()['calls']))
            raise
