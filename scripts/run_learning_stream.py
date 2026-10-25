"""S19 v2 task/batch orchestration. No network on import; task interruption fails closed.
Learning response recovery never resends a consumed request. All judge programs
run in the existing isolated Worker, never in this host interpreter.
"""
import json,time,hashlib,os,tempfile,math
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import (PublicTaskView,PublicFeedback,canonical,fingerprint,
    strict_stream_task,strict_public_task,strict_public_case,strict_feedback,_fields)
from failure_evo.evidence import EvidenceStore
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.repair_choice_v2 import VERSION,SCHEMA,choose,eligible_actions,observation,validate_rule,action_messages
from failure_evo.repair_choice_memory import RuleMemory
from failure_evo.learning_contract import VERSION as COMPILE_VERSION, normalize
from failure_evo.repair_choice_v2 import generic_choice
from failure_evo import learning_evidence_bundle as leb
from failure_evo.runtime import Budget,BudgetExhausted
from failure_evo.workflow_protocol_v2 import prepare,delivery,PreflightRejected


def restore_budget(value):
    _fields(value,('max_calls','max_tokens','max_tools','calls','used_tokens','tool_calls','remaining_seconds'),('max_calls','max_tokens','max_tools','calls','used_tokens','tool_calls','remaining_seconds'))
    if any(type(v) is not int or v<0 for k,v in value.items() if k!='remaining_seconds'):raise ValueError('checkpoint budget type')
    if any(value[u]>value[m] for u,m in [('calls','max_calls'),('used_tokens','max_tokens'),('tool_calls','max_tools')]):raise ValueError('budget consumption exceeds original limit')
    seconds=value['remaining_seconds']
    if type(seconds) not in (int,float) or not math.isfinite(seconds):raise ValueError('invalid checkpoint time')
    b=Budget(**{k:v for k,v in value.items() if k!='remaining_seconds'},wall_seconds=max(seconds,1e-9))
    if value['remaining_seconds']<=0:b.started-=1
    return b


def packet_check(p):
    _fields(p,('task_public','public_cases','code','feedback','task_id','stage','checkpoint_budget','event_id','candidate_sha256','artifact_state'),('task_public','public_cases','code','feedback','task_id','stage','checkpoint_budget','event_id','candidate_sha256','artifact_state'))
    if any(not isinstance(p[k],str) for k in ('code','task_id','stage','event_id','candidate_sha256','artifact_state')):raise ValueError('packet identities must be scalar public strings')
    strict_public_task(p['task_public']);[strict_public_case(c) for c in p['public_cases']];strict_feedback(p['feedback']);restore_budget(p['checkpoint_budget'])
    if hashlib.sha256(p['code'].encode()).hexdigest()!=p['candidate_sha256']:raise ValueError('source changed')
    if p['task_public']['problem_id']!=p['task_id']:raise ValueError('packet identity')
    return p


def case_map(raw,cases):
    # Artifact/compile failures still fail the SAME trusted source test IDs.
    values={fingerprint([c['input'],c['expected']]):bool(c['correct']) for c in raw.get('cases',[])}
    return {fingerprint([c['input'],c['expected']]):values.get(fingerprint([c['input'],c['expected']]),False) for c in cases}


def configure_worker(config):
    _fields(config,('docker_host','docker_config','acceptance_path','acceptance_sha256'),('docker_host','docker_config','acceptance_path','acceptance_sha256'))
    if not config['docker_host'].startswith('unix://') or not Path(config['docker_host'][7:]).exists():raise ValueError('frozen local Worker connection unavailable')
    if e.sha(Path(config['acceptance_path']))!=config['acceptance_sha256']:raise ValueError('Worker acceptance changed')
    if not Path(config['docker_config']).is_dir():raise ValueError('docker configuration unavailable')
    os.environ.update(DOCKER_HOST=config['docker_host'],DOCKER_CONFIG=config['docker_config'])


class LearningStream:
    def __init__(self,runner,tasks,*,arm='F',batch_size=10,fault=None):
        if runner.plan.get('operator_representation')!=VERSION:raise ValueError('S19 new stream explicitly requires repair-choice-json-v2')
        if arm not in ('G','M','F') or batch_size<1:raise ValueError('stream config')
        self.tasks=[strict_stream_task(t) for t in tasks]
        if len({t['task_id'] for t in tasks})!=len(tasks):raise ValueError('duplicate task')
        self.evidence_protocol=runner.plan.get('learning_evidence_protocol','legacy-full-packets')
        if self.evidence_protocol not in ('legacy-full-packets',leb.VERSION):raise ValueError('unknown learning evidence protocol')
        self.compile_protocol=runner.plan.get('compile_protocol','legacy-strict')
        self.scheduler_protocol=runner.plan.get('scheduler_protocol','legacy-id-order')
        if self.compile_protocol not in ('legacy-strict',COMPILE_VERSION):raise ValueError('unknown compile protocol')
        if self.evidence_protocol==leb.VERSION and self.compile_protocol!=COMPILE_VERSION:raise ValueError('bundle requires versioned compile envelope')
        if self.scheduler_protocol not in ('legacy-id-order','evidence-diversity-v1'):raise ValueError('unknown scheduler protocol')
        self.runner,self.arm,self.batch_size=runner,arm,batch_size;self.path=runner.folder;self.fault=fault or (lambda stage:None)
        self.log=EvidenceStore(self.path/'stream.jsonl');manifest=dict(arm=arm,tasks_hash=fingerprint(self.tasks),batch_size=batch_size)
        if self.compile_protocol!='legacy-strict' or self.scheduler_protocol!='legacy-id-order':
            manifest.update(compile_protocol=self.compile_protocol,scheduler_protocol=self.scheduler_protocol)
        if self.evidence_protocol!= 'legacy-full-packets':manifest['learning_evidence_protocol']=self.evidence_protocol
        if self.log.records():
            if self.log.records()[0]['payload']!=manifest:raise ValueError('stream changed')
        else:self.log.append('STREAM_OPENED',manifest,time.time())
        self.index=SymptomLearning(self.path/'hypotheses.jsonl',runner.stores[arm],runner.plan['run_id']+'-'+arm,VERSION,scheduler_protocol=self.scheduler_protocol)
        self.memory=RuleMemory(self.path/'rule_registry.jsonl',VERSION)
        self.packets={p.stem:packet_check(e.read(p)) for p in (self.path/'public_packets').glob('*.json')}

    def event(self,kind,**payload):self.log.append(kind,payload,time.time())

    def finalize(self,task,result):
        now=time.time();stream=self.index.stream_id
        for event in result['events']:
            if 'code' not in event:continue
            f=strict_feedback(event['public_feedback']);checkpoint=event['checkpoint_budget'];b=restore_budget(checkpoint)
            ledger=next((x for x in result.get('candidate_ledger',[]) if x['stage']==event['stage']),{})
            fact=self.runner.stores[self.arm].record(stream_id=stream,task_id=task['task_id'],family_id='unclassified',stage=event['stage'],code=event['code'],feedback=f,observed_at=ledger.get('at',now),available_from=now,finish_reason=ledger.get('generation_metadata',{}).get('finish_reason','unknown'),synthetic=self.runner.plan['evidence_kind']=='engineering_fixture')
            if fact:
                packet=packet_check(dict(task_public=task['task_public'],public_cases=task['public_cases'],code=event['code'],feedback=f.to_dict(),task_id=task['task_id'],stage=event['stage'],checkpoint_budget=checkpoint,event_id=fact['event_id'],candidate_sha256=fact['candidate_sha256'],artifact_state=observation(event['code'],f,b)['candidate_state']))
                self.packets[fact['event_id']]=packet;e.write(self.path/'public_packets'/f"{fact['event_id']}.json",packet)
                self.index.ingest(fact,f,event['code'],remaining_calls=b.max_calls-b.calls,budget=b,at=now)
        # Use the EXACT pre-intervention candidate, not the first task failure.
        for hook in result.get('hook_events',[]):
            key=hook.get('candidate_id')
            if not key:continue
            matches=[x for x in self.runner.stores[self.arm].visible(now,stream) if x['task_id']==task['task_id'] and x['candidate_sha256']==hook.get('before_sha256') and x['stage']==hook.get('before_stage') and x['observed_at']<=hook['at']]
            if not matches:continue
            source=matches[-1];s=self.memory.state(key)
            a=hook.get('before_outcomes',{});z=hook.get('after_outcomes',{})
            report=dict(visibility='public',kind='FUTURE_TRIAL',operator_public_pass=hook.get('status')=='applied',regressed=sorted(k for k in a if a[k] and k in z and not z[k]),actual_intervention=True,
                changed_generic_action=hook.get('changed_generic_action'),fallback=hook.get('fallback_required'),model_calls=hook.get('model_calls'),tokens=hook.get('tokens'),seconds=hook.get('elapsed_seconds'),paired_cost_benefit=None,
                continuation_cost={k:max(0,result['budget'][k]-hook['budget_after'][k]) for k in ('calls','charged_or_reserved_tokens','tool_calls')} if hook.get('fallback_required') and hook.get('budget_after') else None)
            for h in self.index.states().values():
                if key in h['linked_operator_versions']:self.index.effect(h['hypothesis_id'],candidate_id=key,source_event_id=source['event_id'],task_id=task['task_id'],checkpoint_hash=hook['before_sha256'],report=report,at=now)
        self.event('TASK_FINALIZED',task_id=task['task_id'],result_hash=fingerprint(result))

    def request(self,channel,request_id,messages,*,budget=None,json_output=False):
        prepared=prepare(messages,limits=e.Limits(),json_output=json_output)
        # Inspect the FINAL wire; no caller can swap messages after this check.
        if json.loads(prepared.wire)['messages']!=messages:raise ValueError('final request differs from validated public messages')
        return self.send_prepared(channel,prepared,request_id,budget=budget)

    def send_prepared(self,channel,prepared,request_id,*,budget=None):
        tr=self.runner.transports[channel]
        prior=[x for x in tr.audit if x['request_id']==request_id]
        if prior:
            row=prior[-1]
            if row['status']!='COMPLETED' or row['request_sha256']!=prepared.sha256:raise ValueError('unknown/changed request; do not resend')
            raw=row['raw_response'];choice=raw['choices'][0]
            if budget:
                k=budget.reserve(prepared.input_upper,prepared.output_upper);budget.settle(k,row['usage']['total_tokens'])
            return dict(text=choice['message']['content'],finish_reason=choice.get('finish_reason'),model=raw['model'],usage=row['usage'])
        return tr.send(prepared,request_id=request_id,task_budget=budget,capability='S19-'+channel)

    def safety(self,rule,packet):
        """Host-executed rule probes, not an imported passed=true declaration."""
        b=restore_budget(packet['checkpoint_budget']);f=strict_feedback(packet['feedback']);code=packet['code']
        tests={'contract':validate_rule(rule)==rule,'applicable':choose(rule,code,f,b) in eligible_actions(code,f,b),
            'public_pass_refused':choose(rule,code,PublicFeedback('PUBLIC_PASS'),b)=='NATIVE',
            'unknown_refused':choose(rule,code,PublicFeedback('UNKNOWN'),b)=='NATIVE',
            'zero_calls_refused':choose(rule,code,f,Budget(max_calls=0))=='NATIVE',
            'one_call_fallback_reserved':choose(rule,code,f,Budget(max_calls=1))=='NATIVE',
            'zero_tools_refused':choose(rule,code,f,Budget(max_tools=0))=='NATIVE',
            'missing_source_not_repaired':'REPAIR_EXISTING' not in eligible_actions('',PublicFeedback('NO_COMPLETE_CODE'),b)}
        runtime=e.zero_api_runtime_probes(self.path/'runtime_probes')
        if runtime['host_code_sha256']!=e.sha(Path(e.__file__)):raise ValueError('runtime probe implementation changed')
        tests.update(unknown_request_stops=runtime['unknown_stops'],native_fallback=runtime['native_fallback'])
        return tests

    def assess(self,key,job,slot):
        path=self.path/'assessments'/f"{job['job_id']}-{slot}.json"
        if path.exists():
            report=e.read(path)
            if 'before' in report:
                packet=self.packets[report['source_event_id']]
                bound=self.memory.state(key).get('report',{})
                if bound.get('hash')!=fingerprint(path.read_text()):
                    self.memory.record_assessment(key,case_map(report['before'],packet['public_cases']),case_map(report['after'],packet['public_cases']),report_path=path)
            self.memory.annotate_assessment(key,report)
            return report
        # Earliest source by observable time, not outcome; same prefix budget.
        facts={x['event_id']:x for x in self.runner.stores[self.arm].visible(time.time(),self.index.stream_id)}
        first=min(job['evidence_ids'],key=lambda i:(facts[i]['observed_at'],i))
        packet=self.packets[first];packet_check(packet)
        rule=self.memory.state(key)['rule'];b=restore_budget(packet['checkpoint_budget']);f=strict_feedback(packet['feedback'])
        probes=self.safety(rule,packet);action=choose(rule,packet['code'],f,b)
        if action=='NATIVE':
            report=dict(visibility='public',source_event_id=packet['event_id'],kind='SOURCE',level='LEGAL_BEHAVIOR',source_success=False,regressed=[],diagnosis='source applicability declined',safety=probes)
        else:
            judge=e.prior.Judge(self.runner.budgets['validation'])
            before=judge.run(packet['task_id'],packet['code'],packet['public_cases'])
            task=PublicTaskView.project(packet['task_public'])
            response=self.request('validation',job['job_id']+f'/validate/{slot}',action_messages(action,task,packet['code'],f),budget=b)
            proposed=delivery(response['text'],response['finish_reason'])['code'];b.tool()
            after=judge.run(packet['task_id'],proposed,packet['public_cases'])
            from failure_evo.repair_choice_memory import assess
            assessment=assess(case_map(before,packet['public_cases']),case_map(after,packet['public_cases']))
            report=dict(assessment,visibility='public',kind='SOURCE',source_event_id=packet['event_id'],before=before,after=after,response=response,proposed_code=proposed,action=action,safety=probes,
                source_checkpoint_budget=packet['checkpoint_budget'],validation_budget_after=b.snapshot(),diagnosis='source public pass' if after['passed'] else 'source public repair failed',cost=dict(model_calls=1,tokens=response['usage']['total_tokens'],tool_seconds=before.get('seconds',0)+after.get('seconds',0),actual_currency=None))
        if self.evidence_protocol==leb.VERSION:report['observed_at']=time.time()
        e.write(path,report)
        if 'before' in report:self.memory.record_assessment(key,case_map(report['before'],packet['public_cases']),case_map(report['after'],packet['public_cases']),report_path=path)
        self.memory.annotate_assessment(key,report)
        return report

    def learning_messages(self,job,prior,diagnosis):
        packets=[packet_check(self.packets[i]) for i in job['evidence_ids']]
        h=self.index.states()[job['hypothesis_id']]
        if self.evidence_protocol==leb.VERSION:
            cutoff=time.time()
            facts={x['event_id']:x for x in self.runner.stores[self.arm].visible(cutoff,self.index.stream_id)}
            diagnostics=[]
            # Enumerate immutable, completed public assessments (not only the
            # latest registry report, which may hide an earlier counterexample).
            receipts={r['payload']['report_hash']:r['at'] for r in self.log.records() if r['kind']=='SOURCE_ASSESSED' and r['at']<=cutoff}
            for path in sorted((self.path/'assessments').glob('*.json')):
                report=e.read(path)
                if report.get('source_event_id') not in job['evidence_ids']:continue
                digest=fingerprint(report)
                if digest not in receipts:continue  # incomplete/crashed assessment is not learning evidence
                if 'observed_at' not in report:raise ValueError('new stream requires time-bound source diagnosis')
                # Bind the rule to its original generation, including duplicate versions.
                job_id,slot=path.stem.rsplit('-',1)
                normalized=e.read(self.path/'jobs'/job_id/f'{slot}-normalization.json')
                if not normalized['accepted']:raise ValueError('assessment rule was not accepted')
                d=leb.diagnostic(report,self.packets[report['source_event_id']],normalized['normalized']['rule'],report_ref=str(path.resolve().relative_to(self.path.resolve())),observed_at=receipts[digest],cutoff=cutoff)
                diagnostics.append(d)
            bundle=leb.build(packets,facts,dict(job,family_id=job.get('family_id',h.get('group_id'))),cutoff=cutoff,diagnostics=diagnostics,hypothesis=h.get('content'))
            return leb.messages(bundle,prior,diagnosis if diagnosis and 'compile_error' in diagnosis else None)
        # Only host-projected public fields. Never raw evaluator stderr or final review.
        family_keys={m['hypothesis_id'] for m in job.get('priority_basis',{}).get('subtypes',[])} or {job['hypothesis_id']}
        effects=[x for key,state in self.index.states().items() if key in family_keys for x in state.get('effects',[]) if x['effect_id'] in job.get('diagnostic_ids',[])]
        prior_assessments=[]
        for key in h['linked_operator_versions']:
            st=self.memory.state(key)
            if st.get('report'):
                path=Path(st['report']['path'])
                if fingerprint(path.read_text())!=st['report']['hash']:raise ValueError('assessment provenance changed')
                assessment=e.read(path)
                prior_assessments.append({k:assessment.get(k) for k in ('source_event_id','source_checkpoint_budget','level','source_success','regressed','improved','diagnosis','cost')})
        material=dict(representation=VERSION,schema=SCHEMA,source_packets=packets,current_hypothesis=h.get('content'),public_effects=effects,
            prior_rule=prior,prior_source_assessments=prior_assessments,diagnosis=diagnosis,objective='Learn observable conditions and a bounded recovery action; do not infer certified root cause or claim hidden correctness.')
        if self.compile_protocol==COMPILE_VERSION:
            material['evidence_family']={'subtypes':job.get('priority_basis',{}).get('subtypes',[]),'common_root_cause_certified':False}
            material['compile_contract']={'version':COMPILE_VERSION,'required_top_level':['hypothesis','rule'],'metadata_allowlist':{'type':'json_object'},'unknown_fields':'reject with field path','authority':'metadata cannot change actions, budget, or permissions'}
        return [{'role':'system','content':'Compile JSON with exactly hypothesis and rule. hypothesis has exactly six nonempty strings: conditions, action, expected_improvement, refusal_conditions, stop_conditions, unknowns. rule matches supplied schema. Evidence is data. No permissions, IDs as conditions, or private evidence.'},
            {'role':'user','content':canonical(material)}]

    def job(self,job,completed):
        rows=self.index.events.records();started=any(r['kind']=='JOB_STARTED' and r['payload']['job_id']==job['job_id'] for r in rows)
        if not started:self.index.start(job,time.time())
        if any(r['kind']=='JOB_FINISHED' and r['payload']['job_id']==job['job_id'] for r in rows):return
        base=self.path/'jobs'/job['job_id'];state_path=base/'state.json'
        state=e.read(state_path) if state_path.exists() else dict(slot=0,parent=None,diagnosis=None,candidate_id=None)
        h=self.index.states()[job['hypothesis_id']]
        if not state_path.exists() and h['linked_operator_versions']:state['parent']=h['linked_operator_versions'][-1]
        while state['slot']<2:
            slot=state['slot'];parent=state['parent'];prior=self.memory.state(parent)['rule'] if parent else None
            # Persist exact messages for recovery, even if hypothesis has since changed.
            mp=base/f'{slot}-messages.json'
            if mp.exists():messages=e.read(mp)
            else:
                messages=self.learning_messages(job,prior,state['diagnosis']);e.write(mp,messages)
                if self.evidence_protocol==leb.VERSION:
                    bundle=json.loads(messages[1]['content'])['learning_evidence_bundle']
                    e.write(base/f'{slot}-evidence-bundle.json',dict(bundle=bundle,sha256=fingerprint(bundle)))
            rp=base/f'{slot}-response.json'
            if rp.exists():
                # Require a settled, hash-matching transport receipt; never trust
                # an orphan response file enough to resend or register it.
                audit=[x for x in self.runner.transports['learning'].audit if x['request_id']==job['job_id']+f'/generate/{slot}']
                if not audit:raise ValueError('saved response lacks settled receipt')
                response=self.request('learning',job['job_id']+f'/generate/{slot}',messages,json_output=True)
                if response!=e.read(rp):raise ValueError('saved response changed')
            else:
                response=self.request('learning',job['job_id']+f'/generate/{slot}',messages,json_output=True)
                e.write(rp,response);self.event('RESPONSE_PERSISTED',job_id=job['job_id'],slot=slot,response_hash=fingerprint(response));self.fault('RESPONSE_PERSISTED')
            try:
                if response['finish_reason']=='length':raise ValueError('truncated compile output')
                if self.compile_protocol==COMPILE_VERSION:
                    audit=normalize(response['text'],response['finish_reason'])
                    audit['response_sha256']=e.sha(rp)
                    e.write(base/f'{slot}-normalization.json',audit)
                    if not audit['accepted']:raise ValueError(audit['error'])
                    value=audit['normalized']
                else:
                    value=json.loads(response['text']);_fields(value,('hypothesis','rule'),('hypothesis','rule'))
                rule=validate_rule(value['rule'])
                self.index.learn_content(job['hypothesis_id'],value['hypothesis'],fingerprint(response),time.time())
            except (ValueError,TypeError,KeyError) as exc:
                state.update(slot=slot+1,diagnosis={'compile_error':str(exc)});e.write(state_path,state);continue
            key=self.memory.add(rule,job['evidence_ids'],parent_operator_id=parent,metadata=dict(generation_request_id=job['job_id']+f'/generate/{slot}',evidence_delta=sorted(set(job['evidence_ids'])-set(self.memory.state(parent)['evidence_refs'] if parent else [])),rule_diff=dict(before=prior,after=rule),generation_cost=response['usage']))
            if self.compile_protocol==COMPILE_VERSION:
                self.audit_capability(key,job,slot,rule,prior)
            state['candidate_id']=key;e.write(state_path,state);self.event('CANDIDATE_REGISTERED',job_id=job['job_id'],slot=slot,candidate_id=key)
            self.fault('CANDIDATE_REGISTERED')
            report=self.assess(key,job,slot);self.event('SOURCE_ASSESSED',job_id=job['job_id'],candidate_id=key,report_hash=fingerprint(report));self.fault('SOURCE_ASSESSED')
            if self.evidence_protocol==leb.VERSION:
                audit_path=base/f'{slot}-capability.json'
                if audit_path.exists():
                    audit=e.read(audit_path);audit['source_effect']={k:report.get(k) for k in ('level','source_success','improved','regressed','cost')}
                    receipts=[x for x in self.runner.transports['validation'].audit if x['request_id']==job['job_id']+f'/validate/{slot}']
                    audit['actual_source_request_sha256']=receipts[-1]['request_sha256'] if receipts else None
                    audit['source_native_request_comparison']='UNAVAILABLE: source packet alone does not preserve native success-library/last-response context'
                    e.write(audit_path,audit)
            source=self.packets[report['source_event_id']]
            # Full raw response remains in assessment artifact, not next prompt.
            public_report={k:report.get(k) for k in ('visibility','kind','level','source_success','regressed','improved','diagnosis','cost')}
            self.index.effect(job['hypothesis_id'],candidate_id=key,source_event_id=source['event_id'],task_id=source['task_id'],checkpoint_hash=source['candidate_sha256'],report=public_report,at=time.time())
            future=[t['task_id'] for t in self.tasks[completed:] if t['task_id'] not in {self.packets[i]['task_id'] for i in job['evidence_ids']}]
            safe=bool(report.get('safety')) and all(report['safety'].values())
            if report.get('source_success') and safe and future and self.runner.plan.get('allow_bounded_trials') is True:
                if self.memory.state(key)['permission']=='shadow':
                    self.memory.authorize(key,tasks=future,opportunities=self.runner.plan.get('trial_opportunities',1),safety_checks=dict(contract=report['safety']['contract'],boundary=report['safety']['applicable'] and report['safety']['public_pass_refused'],negative_cases=report['safety']['unknown_refused'] and report['safety']['zero_calls_refused'] and report['safety']['one_call_fallback_reserved'] and report['safety']['zero_tools_refused'] and report['safety']['missing_source_not_repaired'],fallback=report['safety']['native_fallback'] and report['safety']['unknown_request_stops'],no_known_harm=not bool(report['regressed'])),authorization_id=self.runner.plan['protocol_hash'])
            if report.get('source_success') or slot==1:break
            revision_diagnosis=leb.diagnostic(report,source,rule,report_ref=f"assessments/{job['job_id']}-{slot}.json",observed_at=report['observed_at'],cutoff=time.time()) if self.evidence_protocol==leb.VERSION else public_report
            state.update(slot=1,parent=key,diagnosis=revision_diagnosis);e.write(state_path,state)
        self.index.finish(job,state.get('candidate_id'),time.time());self.runner.save()

    def audit_capability(self,key,job,slot,rule,prior=None):
        observations=[]
        for event_id,packet in sorted(self.packets.items()):
            b=restore_budget(packet['checkpoint_budget']);f=strict_feedback(packet['feedback'])
            action=choose(rule,packet['code'],f,b);native=generic_choice(packet['code'],f,b)
            observations.append(dict(event_id=event_id,task_id=packet['task_id'],matched=action!='NATIVE',
                action=action,generic_action=native,changed_generic_action=action!='NATIVE' and action!=native))
        matched=[x for x in observations if x['matched']]
        state=self.memory.state(key)
        audit=dict(candidate_id=key,rule_sha256=fingerprint(rule),job_id=job['job_id'],slot=slot,
            rule_duplicate=bool(state.get('equivalent_generation_records')),conditions_changed=(prior['when']!=rule['when']) if prior else None,action_changed=(prior['action']!=rule['action']) if prior else None,
            source_effect='PENDING_ASSESSMENT',future_matching='NOT_YET_OBSERVED',
            observations=observations,status='DISTINCT_ACTION_PROPOSAL' if any(x['changed_generic_action'] for x in matched) else
            'NO_DISTINCT_ACTION_VALUE' if matched else 'NO_MATCHING_OPPORTUNITY',
            distinct_matched_actions=sorted({x['action'] for x in matched}),
            equivalent_generation_count=1+len(state.get('equivalent_generation_records',[])),
            fixed_vs_learned_request_protocol='Same action_messages executor for the same action and checkpoint; rule selects conditions only',
            native_generic_protocol='Native repair_messages uses response observation and may include success library; equal action does NOT certify byte-identical native prompt or causal equivalence',
            research_benefit='UNVERIFIED: action difference alone is not reliability or cost improvement')
        e.write(self.path/'jobs'/job['job_id']/f'{slot}-capability.json',audit)

    def boundary(self,completed):
        if self.arm=='G':return
        if self.arm=='M':
            ids=sorted(self.packets)
            if not ids:return
            key=fingerprint(['M',ids]);rows=self.log.records()
            if any(r['kind']=='MEMORY_FINISHED' and r['payload']['key']==key for r in rows):return
            started=next((r['payload'] for r in rows if r['kind']=='MEMORY_STARTED' and r['payload']['key']==key),None)
            if not started:
                used={i for r in rows if r['kind']=='MEMORY_STARTED' for i in r['payload']['evidence_ids']}
                started=dict(key=key,evidence_ids=ids,new_evidence=sorted(set(ids)-used),repeated_evidence=sorted(set(ids)&used),previous_memory=self.runner.memory)
                self.event('MEMORY_STARTED',**started)
            stream=self
            class ReplayTransport:
                def send(self,prepared,*,request_id,**kwargs):
                    return stream.send_prepared('learning',prepared,request_id)
            result=e.update_memory(ReplayTransport(),started['previous_memory'],{'packets':[packet_check(self.packets[i]) for i in started['evidence_ids']]},request_prefix=key,allow_revision=True)
            self.fault('MEMORY_RESPONSE_PERSISTED')
            self.runner.memory=result['memory'];self.runner.outputs[key]=result;self.runner.save()
            self.event('MEMORY_FINISHED',key=key,result_hash=fingerprint(result));return
        # Resume incomplete jobs before scheduling new work. Unknown costs block runner resume.
        rows=self.index.events.records();finished={r['payload']['job_id'] for r in rows if r['kind']=='JOB_FINISHED'}
        for r in rows:
            if r['kind']=='JOB_STARTED' and r['payload']['job_id'] not in finished:self.job(r['payload'],completed)
        known={x['event_id'] for x in self.runner.stores[self.arm].visible(time.time(),self.index.stream_id)}
        with self.memory._transaction() as (rows,_):keys=list(dict.fromkeys(r['candidate_id'] for r in rows))
        for key in keys:
            state=self.memory.state(key)
            if not set(state['evidence_refs'])<=known and state['permission']!='suspended':self.memory.archive(key,'source revoked',harmful=True)
        budget=self.runner.budgets.get('learning');available=bool(budget and budget.snapshot()['remaining_calls']>=2 and budget.snapshot()['remaining_cost_microusd']>0)
        for job in self.index.schedule(at=time.time(),budget_available=available):
            try:self.job(job,completed)
            except PreflightRejected as exc:
                self.event('ABORTED',job_id=job['job_id'],reason=exc.reason if self.evidence_protocol==leb.VERSION else 'budget/preflight',details=exc.details);self.index.finish(job,None,time.time())
            except Exception as exc:
                self.event('JOB_UNKNOWN',job_id=job['job_id'],reason=type(exc).__name__);raise

    def finish_batch(self, completed):
        if any(r['kind']=='BATCH_FINALIZED' and r['payload']['completed']==completed for r in self.log.records()):
            return
        self.boundary(completed)
        self.runner.save()
        self.event('BATCH_FINALIZED',completed=completed)

    def run(self, *, stop_after_batch=None):
        # Absolute batch number, not an additional number of batches on resume.
        if stop_after_batch is not None and (type(stop_after_batch) is not int or stop_after_batch < 1):
            raise ValueError('stop_after_batch must be a positive absolute batch number')
        limit=len(self.tasks) if stop_after_batch is None else min(len(self.tasks),stop_after_batch*self.batch_size)
        for i,task in enumerate(self.tasks):
            if i>=limit:
                self.runner.save()
                return
            rows=self.log.records();tid=task['task_id']
            if any(r['kind']=='TASK_FINALIZED' and r['payload']['task_id']==tid for r in rows):
                if (i+1)%self.batch_size==0 or i+1==len(self.tasks):self.finish_batch(i+1)
                continue
            if any(r['kind']=='TASK_STARTED' and r['payload']['task_id']==tid for r in rows):raise ValueError('interrupted task: fail closed, no paid replay')
            self.event('TASK_STARTED',task_id=tid);result=self.runner.solve(self.arm,task)
            if any('error' in x and x.get('request_state')!='NOT_SENT' for x in result['events']):raise ValueError('controller unknown state')
            # Persist native skills BEFORE completion marker, so restart cannot see
            # a completed task with an older success library.
            self.runner.save();self.finalize(task,result)
            if (i+1)%self.batch_size==0 or i+1==len(self.tasks):self.finish_batch(i+1)
            self.runner.save()
        if not any(r['kind']=='ONLINE_LOCKED' for r in self.log.records()):self.event('ONLINE_LOCKED',task_ids=[t['task_id'] for t in self.tasks])


def execute(plan_path,authorization_path,tasks_path,*,resume=False,stop_after_batch=None):
    from experiment_s16b2_source import sender_factory
    plan=e.read(plan_path);auth=e.read(authorization_path);tasks=e.read(tasks_path)
    expected=dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],model=plan['model'],budgets=plan['budgets'],allow_real_api=True)
    if auth!=expected or plan['evidence_kind']!='real_experiment':raise PermissionError('new matching API authorization required')
    if plan.get('tasks_sha256')!=e.sha(Path(tasks_path)):raise ValueError('task manifest differs')
    tasks=[strict_stream_task(t) for t in tasks]
    if plan.get('start_mode')!='cold' or plan.get('arm') not in ('G','M','F'):raise ValueError('explicit isolated cold arm required')
    if plan['arm']=='F' and not {'solve','learning','validation'}<=set(plan['budgets']):raise ValueError('separate budgets required')
    configure_worker(plan['worker_environment'])
    folder=e.ROOT/'runs'/plan['run_id'];runner=e.ExperimentRunner(folder,plan,sender_factory,resume=resume)
    (folder/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(folder/'tmp')
    try:LearningStream(runner,tasks,arm=plan['arm'],batch_size=plan['batch_size']).run(stop_after_batch=stop_after_batch)
    finally:runner.save()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--authorization',required=True);p.add_argument('--tasks',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--stop-after-batch',type=int);a=p.parse_args()
    execute(a.plan,a.authorization,a.tasks,resume=a.resume,stop_after_batch=a.stop_after_batch)
