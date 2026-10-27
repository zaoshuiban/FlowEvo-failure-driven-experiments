"""Bounded, persistent learning scheduler. No model or network client is imported."""
import hashlib
import json
from pathlib import Path
from .contracts import fingerprint, canonical
from .evidence import EvidenceStore
from .runtime import BudgetExhausted


class CompileQueue:
    def __init__(self, path, interval=20, max_families=2):
        if type(interval) is not int or interval < 1 or type(max_families) is not int or not 1 <= max_families <= 2:
            raise ValueError('invalid learning schedule')
        self.events = EvidenceStore(path)
        self.interval = interval
        self.max_families = max_families

    def due(self, store, stream_id, completed_tasks, at):
        """First credible fact at task end, then fixed checkpoints; no repeated evidence."""
        if type(completed_tasks) is not int or completed_tasks < 1:
            return ()
        prior = [r['payload'] for r in self.events.visible(at) if r['payload']['stream_id'] == stream_id]
        if prior and completed_tasks % self.interval:
            return ()
        used = {e for row in prior for e in row['evidence_ids']}
        families = {row['family_id'] for row in prior}
        grouped = {}
        for event in store.visible(at, stream_id):
            if event['synthetic'] or event['event_id'] in used:
                continue
            grouped.setdefault(event['family_id'], []).append(event['event_id'])
        jobs = []
        for family, ids in sorted(grouped.items()):
            if family not in families and len(families) >= self.max_families:
                continue
            families.add(family)
            jobs.append(dict(stream_id=stream_id, family_id=family, evidence_ids=ids,
                             job_id=fingerprint([stream_id, family, ids]), completed_tasks=completed_tasks))
        return tuple(jobs)

    def compile(self, job, compiler, budget, *, at, output_upper=4096):
        """Host-injected compiler adapter; first request creates only a Shadow artifact.

        Failed requests are consumed. This is specification induction, not an implicit
        deployment permission. Candidate/revision calls use BoundedCompiler below.
        """
        if any(r['payload']['job_id'] == job['job_id'] for r in self.events.records()):
            raise ValueError('job already attempted')
        # Reserve before recording an attempt, so no budget means no lost queue work.
        key = budget.reserve(len(str(job).encode()) + 4096, output_upper)
        self.events.append('COMPILE_ATTEMPTED', dict(job), at)
        try:
            response = compiler(dict(job))
            budget.settle(key, response.get('usage', {}).get('total_tokens'))
            if budget.remaining_seconds <= 0:
                raise BudgetExhausted('learning deadline exceeded')
            return response
        except BaseException:
            if key in budget.reservations:
                budget.settle(key)
            raise


    def schedule_hypotheses(self, index, *, at, budget_available):
        if getattr(index,'scheduler_protocol','legacy-id-order')=='evidence-diversity-v1':
            return self.schedule_diverse(index,at=at,budget_available=budget_available)
        rows=self.events.records();jobs=[]
        attempts=[r['payload'] for r in rows if r['kind']=='JOB_STARTED']
        active={j['hypothesis_id'] for j in attempts if not any(r['kind']=='JOB_FINISHED' and r['payload']['job_id']==j['job_id'] for r in rows)}
        known={x['event_id'] for x in index.store.visible(at,index.stream_id)}
        for key,s in sorted(index.states().items()):
            evidence=sorted(set(s['source_evidence_ids']+s['contradicting_evidence_ids']+s['supporting_evidence_ids']) & known)
            diagnostics=sorted(x['effect_id'] for x in s.get('effects',[]) if x['source_event_id'] in known)
            prior=[j for j in attempts if j['hypothesis_id']==key]
            used_diagnostics={x for j in prior for x in j.get('diagnostic_ids',[])} | {x for r in rows if r['kind']=='JOB_FINISHED' and r['payload'].get('hypothesis_id')==key for x in r['payload'].get('consumed_diagnostics',[])}
            used={x for j in prior for x in j['evidence_ids']}
            reason = ('NO_BUDGET' if not budget_available else 'NO_ACTION' if not s['applicable_actions'] else
                'NO_NEW_EVIDENCE' if not (set(evidence)-used or set(diagnostics)-used_diagnostics) else 'IN_FLIGHT' if key in active else
                'FAMILY_LIMIT' if len(active)>=self.max_families else '')
            decision='SKIP' if reason else 'REVISE' if prior else 'GENERATE'
            job=dict(job_id=fingerprint([key,evidence,diagnostics]),hypothesis_id=key,evidence_ids=evidence,diagnostic_ids=diagnostics,
                decision=decision,reason=reason,hypothesis_version=s['version'])
            self.events.append('SCHEDULE_DECISION',job,at)
            if not reason:
                self.events.append('JOB_SCHEDULED',job,at);jobs.append(job);active.add(key)
        return jobs

    def schedule_diverse(self,index,*,at,budget_available):
        """Public-prefix-only ranking; family is organizational, never a root cause claim.

        Keep original hypothesis identities; coarse families exclude finish reason
        but preserve artifact/result/actions, so incompatible actions are not merged.
        One representative per family and no overlapping source tasks per boundary.
        """
        rows=self.events.visible(at);states={r['payload']['hypothesis_id']:r['payload'] for r in index.events.visible(at) if r['kind']=='HYPOTHESIS_VERSION'}
        facts={x['event_id']:x for x in index.store.visible(at,index.stream_id)}
        attempts=[r['payload'] for r in rows if r['kind']=='JOB_STARTED']
        finished={r['payload']['job_id'] for r in rows if r['kind']=='JOB_FINISHED'}
        active=[j for j in attempts if j['job_id'] not in finished]
        used_tasks={facts[i]['task_id'] for j in active for i in j['evidence_ids'] if i in facts}
        groups={}
        for key,s in sorted(states.items()):
            symptom={k:v for k,v in s['symptom'].items() if k!='finish_reason'}
            family=fingerprint(symptom);groups.setdefault(family,[]).append((key,s))
        ranked=[]
        for family,members in groups.items():
            ids=sorted({i for _,s in members for i in s['source_evidence_ids']+s['supporting_evidence_ids']+s['contradicting_evidence_ids'] if i in facts})
            tasks=sorted({facts[i]['task_id'] for i in ids})
            # Provenance group is a recorded proxy, NOT certified independent genealogy.
            lineages=sorted({facts[i]['provenance_group_id'] for i in ids})
            keys={k for k,_ in members};prior=[j for j in attempts if j['hypothesis_id'] in keys]
            used={i for j in prior for i in j['evidence_ids']}
            diag=sorted({x['effect_id'] for _,s in members for x in s.get('effects',[]) if x['source_event_id'] in facts})
            consumed={i for j in prior for i in j.get('diagnostic_ids',[])} | {i for r in rows if r['kind']=='JOB_FINISHED' and r['payload'].get('hypothesis_id') in keys for i in r['payload'].get('consumed_diagnostics',[])}
            # Prefer an already learned representative for a revision, otherwise earliest stable ID.
            key,state=min(members,key=lambda kv:(not bool(kv[1]['linked_operator_versions']),kv[0]))
            novelty=sorted(set(ids)-used);new_tasks={facts[i]['task_id'] for i in novelty}-{facts[i]['task_id'] for i in used if i in facts}
            score=(len(tasks),len(lineages),len(new_tasks),int(len(state['applicable_actions'])>1),-len(prior))
            basis=dict(independent_task_ids=tasks,provenance_group_ids=lineages,provenance_is_independence_proof=False,
                fresh_task_count=len(new_tasks),visible_evidence_count=len(ids),actions=state['applicable_actions'],
                previous_attempt_count=len(prior),subtypes=[dict(hypothesis_id=k,finish_reason=s['symptom']['finish_reason']) for k,s in members],
                native_recovery_cost='NOT_RANKED: no prefix-bound comparable recovery cost supplied',
                equivalent_rule_handling='RuleMemory deduplicates accepted rules; no-new-evidence blocks repeat compilation',
                no_common_root_cause_claim=True)
            ranked.append((score,family,key,state,ids,diag,prior,novelty,set(diag)-consumed,basis))
        ranked.sort(key=lambda r:(tuple(-x for x in r[0]),r[1]))
        jobs=[]
        for rank,(_,family,key,state,ids,diag,prior,novelty,new_diag,basis) in enumerate(ranked,1):
            tasks=set(basis['independent_task_ids'])
            reason=('NO_BUDGET' if not budget_available else 'NO_ACTION' if not state['applicable_actions'] else
                'NO_NEW_EVIDENCE' if not (novelty or new_diag) else
                'IN_FLIGHT' if any(j['hypothesis_id'] in {m['hypothesis_id'] for m in basis['subtypes']} for j in active) else
                'SOURCE_DIVERSITY_LIMIT' if tasks & used_tasks else
                'FAMILY_LIMIT' if len(active)+len(jobs)>=self.max_families else '')
            job=dict(job_id=fingerprint(['evidence-diversity-v1',family,ids,diag]),hypothesis_id=key,
                evidence_ids=ids,diagnostic_ids=diag,decision='SKIP' if reason else 'REVISE' if prior else 'GENERATE',
                reason=reason,hypothesis_version=state['version'],family_id=family,priority_rank=rank,priority_basis=basis,
                scheduler_protocol='evidence-diversity-v1')
            self.events.append('SCHEDULE_DECISION',job,at)
            if not reason:
                self.events.append('JOB_SCHEDULED',job,at);jobs.append(job);used_tasks.update(tasks)
        return jobs


class BoundedCompiler:
    """Per-study 2 families × (1 induction + 3 candidates + 3 revisions) ceiling."""
    def __init__(self, provider, budget, path, model, *, max_input_upper=65536, max_output_upper=4096):
        if budget.max_calls > 14:
            raise ValueError('generation budget exceeds 14 requests')
        self.provider, self.budget, self.model = provider, budget, model
        if any(type(v) is not int or v < 1 for v in (max_input_upper, max_output_upper)):
            raise ValueError('positive compiler token ceilings required')
        self.max_input_upper, self.max_output_upper = max_input_upper, max_output_upper
        self.events = EvidenceStore(path)
        self.artifacts = Path(path).parent / 'generated_artifacts'

    def import_specification(self, job, source_path, at):
        """Bind an explicitly reviewed saved specification; no model request occurred."""
        source=Path(source_path).resolve();content=source.read_text()
        if not content.strip():raise ValueError('empty imported specification')
        own=[r for r in self.events.records() if
             (r['payload'].get('stream_id'),r['payload'].get('family_id'))==(job['stream_id'],job['family_id'])]
        if own:raise ValueError('family already initialized; do not replace its specification')
        self.events.append('SPECIFICATION_IMPORTED',dict(stream_id=job['stream_id'],
            family_id=job['family_id'],phase='induction',content=content,
            source_path=str(source),content_sha256=hashlib.sha256(content.encode()).hexdigest(),
            origin='host_reviewed_saved_specification',new_model_calls=0),at)
        return content

    def import_candidate(self, job, slot, source_path, response_path, at):
        """Import a real failed artifact for a NEW diagnostic run; never a new generation."""
        from .model_api import validate_compile_output
        source, response_file = Path(source_path).resolve(), Path(response_path).resolve()
        saved = json.loads(response_file.read_text())
        response = saved.get('response', saved)
        choice = response['raw_response']['choices'][0]
        value = json.loads(choice['message']['content'])
        code = source.read_text()
        if not code.strip() or value.get('code') != code or slot not in (0, 1, 2):
            raise ValueError('imported source differs from raw model response')
        rows = self.events.records()
        if any(r['payload'].get('stream_id') == job['stream_id'] and
               r['payload'].get('family_id') == job['family_id'] and
               r['payload'].get('phase') == 'candidate' and r['payload'].get('slot') == slot for r in rows):
            raise ValueError('candidate slot already imported/generated')
        review = validate_compile_output(value, choice['finish_reason'])
        payload = dict(stream_id=job['stream_id'], family_id=job['family_id'], phase='candidate', slot=slot,
            content=code, content_sha256=hashlib.sha256(code.encode()).hexdigest(),
            source_path=str(source), response_path=str(response_file), response_sha256=hashlib.sha256(response_file.read_bytes()).hexdigest(),
            origin='saved_model_candidate_diagnostic_import', new_model_calls=0,
            model=response.get('model'), response_id=response.get('id'))
        self.events.append('CANDIDATE_IMPORTED', payload, at)
        self.events.append('CANDIDATE_STATIC_REVIEW', dict(stream_id=job['stream_id'], family_id=job['family_id'],
            slot=slot, phase='candidate', artifact_sha256=payload['content_sha256'], review=review), at)
        return review

    def request(self, job, phase, slot, at, output_upper=4096):
        rows = [r['payload'] for r in self.events.records() if r['kind']=='GENERATION_REQUESTED']
        family = (job['stream_id'], job['family_id'])
        keys = {(r['stream_id'], r['family_id']) for r in rows}
        if family not in keys and len(keys) >= 2:
            raise ValueError('family limit reached')
        if phase not in ('induction', 'candidate', 'revision') or type(slot) is not int:
            raise ValueError('unknown generation phase')
        if (phase == 'induction' and slot != 0) or (phase != 'induction' and slot not in (0, 1, 2)):
            raise ValueError('candidate slot limit reached')
        completed = [r['payload'] for r in self.events.records() if r['kind'] in ('GENERATION_COMPLETED','SPECIFICATION_IMPORTED','CANDIDATE_IMPORTED')]
        own_completed = [r for r in completed if (r['stream_id'],r['family_id'])==family]
        for record in own_completed:
            if record.get('origin') == 'saved_model_candidate_diagnostic_import':
                if (hashlib.sha256(Path(record['source_path']).read_bytes()).hexdigest() != record['content_sha256']
                        or hashlib.sha256(Path(record['response_path']).read_bytes()).hexdigest() != record['response_sha256']):
                    raise ValueError('imported candidate provenance changed')
            if record.get('origin')=='host_reviewed_saved_specification':
                if hashlib.sha256(Path(record['source_path']).read_bytes()).hexdigest()!=record['content_sha256']:
                    raise ValueError('imported specification changed')
                if phase in ('candidate','revision') and job.get('specification')!=record['content']:
                    raise ValueError('request differs from imported specification')
        own = [r for r in rows if (r['stream_id'], r['family_id']) == family]
        if any(r['phase'] == phase and r['slot'] == slot for r in own):
            raise ValueError('generation request already consumed')
        if phase != 'induction' and not any(r['phase'] == 'induction' for r in own_completed):
            raise ValueError('induction must precede candidates')
        if phase == 'revision' and not any(r['phase'] == 'candidate' and r['slot'] == slot for r in own_completed):
            raise ValueError('candidate must precede revision')
        if phase == 'revision' and 'revision_parent' in job:
            parent = job['revision_parent']
            candidate = next(r for r in own_completed if r['phase']=='candidate' and r['slot']==slot)
            if (parent.get('slot') != slot or parent.get('code') != candidate['content'] or
                    parent.get('sha256') != candidate['content_sha256']):
                raise ValueError('revision parent differs from original model artifact')
            reviews = [r['payload'] for r in self.events.records() if r['kind']=='CANDIDATE_STATIC_REVIEW'
                       and r['payload']['stream_id']==family[0] and r['payload']['family_id']==family[1]
                       and r['payload']['slot']==slot and r['payload']['phase']=='candidate']
            if (len(reviews)!=1 or job.get('static_diagnostics')!=reviews[0]['review'] or
                    job.get('static_diagnostics_sha256')!=fingerprint(reviews[0]['review'])):
                raise ValueError('revision diagnostics differ from recorded static review')
        if phase == 'revision' and 'functional_diagnostics' in job:
            functional = [r['payload'] for r in self.events.records() if r['kind']=='CANDIDATE_FUNCTIONAL_REVIEW'
                          and r['payload']['stream_id']==family[0] and r['payload']['family_id']==family[1]
                          and r['payload']['slot']==slot and r['payload']['phase']=='candidate']
            if (len(functional)!=1 or job['functional_diagnostics'] != functional[0]['review']
                    or job.get('functional_diagnostics_sha256') != fingerprint(functional[0]['review'])):
                raise ValueError('revision functional diagnostics differ from host review')
        request = dict(job, phase=phase, slot=slot, max_tokens=output_upper)
        # Providers exposing the final wire own serialization, including prompts
        # and schema. Count that representation once; internal job metadata is
        # not another model input. Keep the legacy estimate only for providers
        # without a wire preparation interface. These are conservative bounds,
        # not tokenizer measurements or provider-reported usage.
        input_upper = len(str(request).encode()) + 4096
        input_basis = 'legacy-request-repr-plus-4096'
        prepare = getattr(self.provider, 'preflight', None) or getattr(self.provider, 'prepare', None)
        if callable(prepare):
            wire = prepare(request)
            input_upper = len(canonical(wire).encode()) + 256
            input_basis = 'final-wire-utf8-plus-256-v1'
        if (type(output_upper) is not int or not 0 < output_upper <= self.max_output_upper
                or input_upper > self.max_input_upper):
            raise BudgetExhausted('request exceeds frozen compiler token ceilings')
        if hasattr(self.budget, 'consume_shard'):
            key = self.budget.reserve(input_upper, output_upper,
                job_id=job.get('job_id', fingerprint(job)), capability='generation:'+phase,
                request_id=fingerprint(['generation',family,phase,slot]), request_hash=fingerprint(request))
        else:
            key = self.budget.reserve(input_upper, output_upper)
        self.events.append('GENERATION_REQUESTED', request, at)
        if callable(prepare):
            self.events.append('WIRE_PREFLIGHT', dict(request_sha256=fingerprint(request),
                wire_sha256=fingerprint(wire), wire_bytes=len(canonical(wire).encode()),
                input_token_upper=input_upper, output_token_upper=output_upper,
                input_accounting=input_basis), at)
        try:
            response = self.provider(request)
            # Preserve returned failures/model drift too, before validation or settlement.
            self.events.append('GENERATION_RESPONSE', dict(request_sha256=fingerprint(request),
                response=response), at)
            if hasattr(self.budget, 'consume_shard'):
                self.budget.settle(key, response.get('usage', {}).get('total_tokens'),
                    cost_microusd=response.get('actual_cost_microusd'))
            else:
                self.budget.settle(key, response.get('usage', {}).get('total_tokens'))
            if response.get('model') != self.model:
                raise ValueError('compiler model drift')
            if self.budget.remaining_seconds <= 0:
                raise BudgetExhausted('compiler exceeded deadline')
            if str(response.get('parse_status','')).startswith('COMPILE_OUTPUT_'):
                rejected = response.get('rejected_compile_output')
                repairable = (response['parse_status']=='COMPILE_OUTPUT_CONTRACT_ERROR'
                              and response.get('finish_reason')=='stop' and isinstance(rejected,dict)
                              and isinstance(rejected.get('code'),str) and rejected['code'].strip()
                              and response.get('code')==rejected['code'])
                if not repairable:
                    raise ValueError(response['parse_status'])
            content = response.get('specification') if phase=='induction' else response.get('code')
            if not isinstance(content,str) or not content.strip():
                raise ValueError('compiler returned no specification/artifact')
            self.artifacts.mkdir(parents=True,exist_ok=True)
            artifact = self.artifacts / (fingerprint(request) + ('.txt' if phase=='induction' else '.py'))
            artifact.write_text(content)
            # Persist successful model provenance and content, without granting execution.
            self.events.append('GENERATION_COMPLETED', dict(stream_id=job['stream_id'],
                family_id=job['family_id'], phase=phase, slot=slot, request_sha256=fingerprint(request),
                model=response.get('model'), response_id=response.get('id'),
                content=content, artifact_path=str(artifact.resolve()),
                content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                usage=response.get('usage', {}), status=('draft_compile_contract_rejected' if response.get('rejected_compile_output') else 'draft')), at)
            return response
        finally:
            if key in self.budget.reservations:
                self.budget.settle(key)
