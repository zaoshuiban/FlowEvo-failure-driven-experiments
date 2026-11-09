"""Action hook and actual environment validation for generated ALFWorld policies."""
import time
from pathlib import Path
from dataclasses import asdict

from alfworld_.env import AlfWorldEnv
from runtime.config import GenerationSettings
from alfworld_.executor import AlfWorldExecutor
from alfworld_.generator import AlfWorldGenerator, AlfWorldStepOutput
from alfworld_.failure_learning import VERSION, context_view
from failure_evo.contracts import canonical,fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_registry import ENVIRONMENT_HOOK,FailureOperator
from failure_evo.math_stream import save
from failure_evo.run_health import RunUnhealthy


class PolicyGenerator:
    """Only the host holds registration, admission and quota handles."""
    def __init__(self,native,registry,runner,*,stream_id,experiment_id,task_id,sequence,
                 events,engineering=False,validation_card=None):
        self.native,self.registry,self.runner=native,registry,runner
        self.stream_id,self.experiment_id,self.task_id,self.sequence=stream_id,experiment_id,task_id,sequence
        self.events=events
        self.engineering=engineering
        self.validation_card=validation_card
        self.states={}
        self.claims={}
        self.used=[]
        self.errors=set()
        self.costs={}

    def step(self,task_goal,observation,admissible_commands,action_history=None,observation_history=None,
             skill_context='',policy_directives=None):
        actions=action_history or []
        observations=observation_history or []
        history=[dict(action=a,observation=observations[i]) for i,a in enumerate(actions)]
        if self.validation_card is not None:
            cards=[self.validation_card]
        elif self.experiment_id=='NO_PERMISSIONS':
            cards=[]
        else:
            snapshot=self.registry.snapshot(stream_id=self.stream_id,task_index=self.sequence,
                                            experiment_id=self.experiment_id,at=time.time())
            cards=list(snapshot.cards)
            for card,_ in self.claims.values():
                if self.registry.valid(card,time.time()) and card not in cards:
                    cards.append(card)
        proposals=[]
        for card in cards:
            if card.operator_kind!='environment_policy' or card.version in self.errors:
                continue
            if card.evidence_fingerprint.model=='MOCK' and not self.engineering:
                raise PermissionError('Mock policy cannot affect a real episode')
            sources={e['task_id'] for e in self.registry.evidence.visible(time.time())
                     if e['event_id'] in card.evidence_ids}
            if self.validation_card is None and self.task_id in sources:
                continue
            context=context_view(task_goal,observation,admissible_commands,history,self.states.get(card.version,{}))
            if self.validation_card is None and card.version not in self.claims:
                token=self.registry.reserve_opportunity(card,stream_id=self.stream_id,
                    experiment_id=self.experiment_id,task_index=self.sequence,task_id=self.task_id,
                    checkpoint='episode',hook=ENVIRONMENT_HOOK,program_sha256=fingerprint(task_goal),at=time.time())
                if not token:
                    continue
                self.claims[card.version]=(card,token)
            old_tools=self.runner.budget.tool_calls
            started=time.monotonic()
            result=self.runner.run(card,context)
            cost=self.costs.setdefault(card.version,dict(tool_calls=0,elapsed_seconds=0.0))
            cost['tool_calls']+=self.runner.budget.tool_calls-old_tools
            cost['elapsed_seconds']+=time.monotonic()-started
            self.states[card.version]=result['state']
            if result['status']=='error':
                self.errors.add(card.version)
                if self.validation_card is None:
                    self.registry.suspend(card,result['reason'],time.time())
                continue
            if result['status']=='applied':
                proposals.append((card,result))
        if proposals and len({result['action'] for _,result in proposals})==1:
            card,result=proposals[0]
            self.used.append((len(actions),card.version,result['action']))
            self.events.append('ENVIRONMENT_ACTION_SELECTED',dict(task_id=self.task_id,sequence=self.sequence,
                step=len(actions),candidate_version=card.version,action=result['action'],
                source_event_ids=list(card.evidence_ids),validation=self.validation_card is not None),time.time())
            return AlfWorldStepOutput(action=result['action'],model_calls=0)
        if len(proposals)>1:
            self.events.append('ENVIRONMENT_POLICY_CONFLICT',dict(task_id=self.task_id,step=len(actions),
                versions=[c.version for c,_ in proposals]),time.time())
        return self.native.step(task_goal,observation,admissible_commands,action_history,observation_history,
                                skill_context,policy_directives)

    def finalize(self,trace):
        actual=[(step,version,action) for step,version,action in self.used
                if step<len(trace.actions) and trace.actions[step].action==action]
        trace.used_skills=sorted({v for _,v,_ in actual})
        trace.direct_use_count=len(actual)
        trace.skill_hit=bool(actual)
        trace.direct_failure_count=len(self.errors)
        trace.runtime_skill_block_reason='POLICY_RUNTIME_ERROR' if self.errors else ''
        for version,(card,token) in self.claims.items():
            used=any(v==version for _,v,_ in actual)
            outcome=dict(status='error' if version in self.errors else 'applied' if used else 'declined',
                         reason='action legality checked; task won='+str(trace.success),
                         actual_cost=dict(**self.costs.get(version,dict(tool_calls=0,elapsed_seconds=0)),model_calls=0))
            if used and version not in self.errors:
                outcome['public_check_outcome']='passed'
            # Existing ledger admission is one reservation per episode, not per action.
            if not any(r['kind']=='OPPORTUNITY_COMPLETED' and r['payload']['reservation_id']==token
                       for r in self.registry.events.records()):
                self.registry.complete_opportunity(card,token,outcome=outcome,at=time.time())
        self.events.append('ENVIRONMENT_POLICY_EPISODE',dict(task_id=self.task_id,sequence=self.sequence,
            won=trace.success,actual_operator_actions=len(actual),candidate_versions=trace.used_skills,
            model_calls=trace.llm_call_count),time.time())


def execute_episode(row,data_root,client,*,registry,runner,stream_id,experiment_id,sequence,
                    events,engineering=False,validation_card=None,max_steps=50):
    env=AlfWorldEnv(split=row.get('split','eval_out_of_distribution'),alfworld_data=str(data_root),max_steps=max_steps)
    try:
        path=str(Path(data_root)/row['game'])
        env.initialize(frozen_game_files=[path])
        task,observation,commands=env.reset()
        if task.game_file!=path:
            raise PermissionError('reset differs from frozen game')
        task.task_id=row['task_id']
        client.begin(task.task_id)
        generator=PolicyGenerator(AlfWorldGenerator(client,GenerationSettings(temperature=0,max_output_tokens=client.config['output_tokens'])),registry,runner,stream_id=stream_id,
                    experiment_id=experiment_id,task_id=task.task_id,sequence=sequence,events=events,
                    engineering=engineering,validation_card=validation_card)
        trace=AlfWorldExecutor(env,generator,max_steps=max_steps).run(task,observation,commands)
        client.health()
        if trace.failure_type.startswith('llm_error'):
            raise RunUnhealthy(trace.failure_type)
        generator.finalize(trace)
        return trace,observation
    finally:
        env.close()


def validate_and_publish(card,source,gate_rows,*,root,data_root,registry,runner,client_factory,
                         stream_id,experiment_id,after_sequence,engineering=False):
    """All permissions come from the existing paired independent Gate API."""
    if not card.intact() or not gate_rows or set(r['task_id'] for r in gate_rows)&{source['task_id']}:
        raise PermissionError('validation roles or source changed')
    facts={e['event_id']:e for e in registry.evidence.visible(time.time())}
    source_tasks={facts[eid]['task_id'] for eid in card.evidence_ids if eid in facts}
    gate_groups={'game:'+r['game_sha256'] for r in gate_rows}
    if (source['task_id'] not in source_tasks
            or 'game:'+source['game_sha256'] not in card.source_group_ids
            or len(gate_groups)!=len(gate_rows)
            or gate_groups & set(card.source_group_ids)
            or len({r['task_id'] for r in gate_rows})!=len(gate_rows)):
        raise PermissionError('independent Gate overlaps learning provenance')
    identity=dict(candidate_version=card.version,source=source,gates=gate_rows,worker=runner.backend.manifest(),
                  effective_after=after_sequence,engineering=engineering)
    events=EvidenceStore(root/'validation.jsonl')
    rows=events.records()
    if rows:
        if rows[0]['payload']!=identity:
            raise PermissionError('candidate validation freeze differs')
        completed=[r['payload'] for r in rows if r['kind']=='ALFWORLD_VALIDATION_DONE']
        if completed:
            return completed[-1]
        raise RunUnhealthy('interrupted environment validation; no repeated Gate probing')
    events.append('ALFWORLD_VALIDATION_STARTED',identity,time.time())
    stage_events=EvidenceStore(root/'policy_execution.jsonl')
    started=time.monotonic()
    source_generic,_=execute_episode(source,data_root,client_factory('source-G'),registry=registry,runner=runner,
                     stream_id=stream_id,experiment_id='NO_PERMISSIONS',sequence=after_sequence,
                     events=stage_events,engineering=engineering)
    source_trace,_=execute_episode(source,data_root,client_factory('source-F'),registry=registry,runner=runner,
                     stream_id=stream_id,experiment_id=experiment_id,sequence=after_sequence,
                     events=stage_events,engineering=engineering,validation_card=card)
    save(root/'source_traces.private.json',dict(G=asdict(source_generic),F=asdict(source_trace)))
    if not source_trace.success or not source_trace.direct_use_count or source_trace.direct_failure_count:
        result=dict(status='SHADOW_SOURCE_NOT_REPAIRED',source_won=source_trace.success,source_generic_won=source_generic.success)
        events.append('ALFWORLD_VALIDATION_DONE',result,time.time())
        return result
    paired=[]
    for row in gate_rows:
        g,_=execute_episode(row,data_root,client_factory('G-'+row['task_id']),registry=registry,runner=runner,
                     stream_id=stream_id,experiment_id='NO_PERMISSIONS',sequence=after_sequence,
                     events=stage_events,engineering=engineering)
        f,_=execute_episode(row,data_root,client_factory('F-'+row['task_id']),registry=registry,runner=runner,
                     stream_id=stream_id,experiment_id=experiment_id,sequence=after_sequence,
                     events=stage_events,engineering=engineering,validation_card=card)
        save(root/('gate-'+row['task_id']+'.private.json'),dict(G=asdict(g),F=asdict(f)))
        paired.append(dict(problem_id=row['task_id'],checkpoint_id=row['game_sha256'],
            source_group='game:'+row['game_sha256'],baseline_correct=g.success,operator_correct=f.success,
            baseline_cost=g.llm_call_count,operator_cost=f.llm_call_count,
            actual_operator_actions=f.direct_use_count,policy_errors=f.direct_failure_count))
    # Denominator and candidate match are fixed before any score is observed.
    wins=sum(bool(p['operator_correct'] and not p['baseline_correct'] and p['actual_operator_actions']) for p in paired)
    regressions=sum(p['baseline_correct'] and not p['operator_correct'] for p in paired)
    savings=sum(bool(p['operator_correct'] and p['baseline_correct'] and p['operator_cost']<p['baseline_cost']
                and p['actual_operator_actions']) for p in paired)
    passed=not regressions and not any(p['policy_errors'] for p in paired) and (wins>0 or savings>=2)
    result=dict(status='QUALIFIED' if passed else 'SHADOW_GATE_NOT_QUALIFIED',paired=paired,
                source_won=True,source_generic_won=source_generic.success,elapsed_seconds=time.monotonic()-started)
    if passed:
        gate=dict(role='PILOT_ADMISSION',shard_id=fingerprint(identity),frozen_before_evaluation=True,
            independent_validation=True,contract_checks_passed=True,scope_checks_passed=True,
            generation_data_isolated=True,operator_id=card.operator_id,version=card.version,
            artifact_sha256=card.artifact_sha256,fingerprint=asdict_fingerprint(card),
            scope=card.evidence_scope,evidence_ids=list(card.evidence_ids),experiment_id=experiment_id,
            evaluated_at=time.time(),validation_source_groups=[p['source_group'] for p in paired],
            regression_passed=True,paired_results=paired,benefit_route='reliability' if wins else 'efficiency',
            cost_unit='model_calls')
        save(root/'gate.json',gate)
        registry.authorize_experiment(card,root/'gate.json',experiment_id=experiment_id,stream_id=stream_id,
                                      after_task=after_sequence,effective_from=after_sequence+1,at=time.time())
    events.append('ALFWORLD_VALIDATION_DONE',result,time.time())
    return result


def asdict_fingerprint(card):
    return card.evidence_fingerprint.to_dict()
