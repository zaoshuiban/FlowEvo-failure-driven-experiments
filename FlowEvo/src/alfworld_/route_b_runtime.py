"""Opt-in bridge to the native full_library generator, using PolicyGenerator.

No candidate creation/admission; no mathematical/environment recovery rules.
Only a generic real no-effect receipt opens a bounded recovery opportunity.
Do not call PolicyGenerator.finalize on the original native trace: it overwrites
native L1 accounting. Persist recovery accounting separately.
"""
from copy import deepcopy
from failure_evo.contracts import fingerprint
from failure_evo.run_health import RunUnhealthy

VERSION='route-b-native-bridge-v1'


class RecoveryBridge:
    def __init__(self,policy,*,episode_limit=50,window=18,max_opportunities=2):
        if not 1<=window<=episode_limit or not 0<=max_opportunities<=2:raise ValueError('unfrozen recovery limits')
        self.policy=policy;self.native=policy.native;self.episode_limit=episode_limit
        self.window=window;self.max_opportunities=max_opportunities
        self.active=False;self.opportunities=0;self.branch_actions=0
        self.seen=set();self.rows=[];self.problem=None

    def step(self,**kwargs):
        history=kwargs.get('action_history') or []
        if len(history)>=self.episode_limit:
            self.problem=RunUnhealthy('shared environment budget exhausted');raise self.problem
        anchor=fingerprint([kwargs['task_goal'],history,kwargs.get('observation_history') or [],kwargs['observation']])
        new_failure=bool(history and kwargs['observation'].strip()=='Nothing happens.' and anchor not in self.seen)
        if not self.active and new_failure and self.opportunities<self.max_opportunities:
            self.active=True;self.opportunities+=1;self.branch_actions=0;self.seen.add(anchor)
            self.policy.states.clear()
        if self.active and self.branch_actions>=self.window:self.active=False
        if not self.active:
            return self.native.step(**kwargs)
        used=len(self.policy.used)
        try:result=self.policy.step(**kwargs)
        except BaseException as exc:
            # Infra errors must not be disguised as a native failure/fallback.
            self.problem=exc;raise
        applied=len(self.policy.used)>used
        if applied:
            if result.action not in kwargs['admissible_commands']:
                self.problem=RunUnhealthy('runner returned an illegal action');raise self.problem
            self.branch_actions+=1
        else:self.active=False
        self.rows.append(dict(checkpoint_sha256=anchor,environment_step=len(history),
            recovery_action_selected=applied,action=result.action,model_calls=result.model_calls,
            native_fallback=not applied,branch_actions=self.branch_actions,errors=sorted(self.policy.errors)))
        return result

    def finish(self,trace):
        if self.problem:raise self.problem
        # Existing Registry quota settlement and policy audit, on a copy only.
        self.policy.finalize(deepcopy(trace))
        executed=sum(r['recovery_action_selected'] and r['environment_step']<len(trace.actions)
            and trace.actions[r['environment_step']].action==r['action'] for r in self.rows)
        return dict(version=VERSION,opportunities=self.opportunities,
            selected_actions=sum(r['recovery_action_selected'] for r in self.rows),actual_actions=executed,
            native_fallbacks=sum(r['native_fallback'] for r in self.rows),
            errors=sorted(self.policy.errors),rows=self.rows,
            native_trace_accounting_preserved=True)
