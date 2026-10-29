"""Opt-in mathematics workflow. No scorer is reachable while choosing an answer."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore

VERSION = 'flowevo-math-no-gold-v1'

@dataclass(frozen=True, slots=True)
class PublicMathTask:
    task_id: str
    problem: str

    def __post_init__(self):
        if not isinstance(self.task_id,str) or not self.task_id or not isinstance(self.problem,str) or not 1 <= len(self.problem) <= 24000:
            raise ValueError('bounded public task identity and problem required')

    @classmethod
    def parse(cls, value):
        if not isinstance(value,dict) or set(value) != {'task_id','problem'}:
            raise ValueError('private or unknown math task fields')
        return cls(**value)

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class NoGoldPolicy:
    reflection_calls: int = 1
    temperature: float = 0.0
    output_tokens: int = 4096
    input_upper: int = 32768
    operators_enabled: bool = False
    delivery_profile: str = "legacy"

    def __post_init__(self):
        if self.delivery_profile not in ('legacy','concise-v1'):raise ValueError('unknown frozen delivery profile')
        if type(self.reflection_calls) is not int or not 0 <= self.reflection_calls <= 1:
            raise ValueError('freeze zero or one unconditional self-review')
        if not 0 <= self.temperature <= 2 or not 1 <= self.output_tokens <= 8192 or not 1 <= self.input_upper <= 65536:
            raise ValueError('invalid frozen solver budget')

SOLVER_SYSTEM = 'You are an expert mathematician. Solve the supplied problem. Give your final answer on a separate line: The answer is [answer].'
REVIEW_SYSTEM = 'Review your own mathematical solution. No external correctness feedback is available. Check the reasoning and return your final answer on a separate line: The answer is [answer].'

CONCISE_SOLVER_SYSTEM = 'Solve the mathematical problem carefully. Keep the explanation concise. Do not print exhaustive intermediate enumerations or unfinished scratch work. Reserve space for a complete final answer. End with a separate line: The answer is <value>. Do not include literal angle brackets.'
CONCISE_REVIEW_SYSTEM = 'Review your previous unverified solution without external correctness feedback. Keep the explanation concise and avoid exhaustive intermediate enumeration. Give a complete final answer within the output budget. End with a separate line: The answer is <value>. Do not include literal angle brackets.'

def solver_messages(task, previous=None, *, profile='legacy'):
    if not isinstance(task,PublicMathTask):raise TypeError('public projection required')
    # No task ID, role, seed, family, reference solution, grade or gold in content.
    content='Problem:\n'+task.problem
    if previous is not None:content+='\n\nYour previous attempt (unverified):\n'+previous
    if profile not in ('legacy','concise-v1'):raise ValueError('unknown delivery profile')
    system=(SOLVER_SYSTEM if previous is None else REVIEW_SYSTEM) if profile=='legacy' else (CONCISE_SOLVER_SYSTEM if previous is None else CONCISE_REVIEW_SYSTEM)
    return [dict(role='system',content=system),dict(role='user',content=content)]

class NoGoldMathController:
    def __init__(self, client, journal, *, policy=NoGoldPolicy(), library=None):
        self.client=client;self.events=EvidenceStore(journal);self.policy=policy;self.library=library

    def solve(self, task, *, episode_id, sequence):
        if not isinstance(task,PublicMathTask):raise TypeError('public task required')
        if any(r['payload'].get('episode_id')==episode_id for r in self.events.records()):
            raise RuntimeError('consumed episode; interruption requires audit, never resend')
        self.events.append('MATH_TASK_STARTED',dict(episode_id=episode_id,task_id=task.task_id,sequence=sequence,protocol=VERSION,policy=asdict(self.policy),gold_exposed=False),time.time())
        started=time.monotonic();op_rows=[];responses=[];output=None
        if self.policy.operators_enabled and self.library is not None:
            op_rows=self.library.run(task,sequence=sequence)
            if op_rows and op_rows[-1]['status']=='APPLIED':output=op_rows[-1]['answer']
        if output is None:
            for step in range(1+self.policy.reflection_calls):
                messages=solver_messages(task,output,profile=self.policy.delivery_profile)
                response=self.client.generate_no_gold(messages=messages,policy=self.policy,request_id=f'{episode_id}/s{step}')
                if not isinstance(response.get('text'),str):raise ValueError('solver delivery contract')
                responses.append(response);output=response['text']
        result=dict(episode_id=episode_id,task_id=task.task_id,sequence=sequence,final_output=output,
            selection='first_applied_operator' if op_rows and op_rows[-1]['status']=='APPLIED' else 'last_scheduled_response',
            responses=responses,operator_events=op_rows,model_calls=len(responses),
            input_tokens=sum(r['usage']['prompt_tokens'] for r in responses),
            output_tokens=sum(r['usage']['completion_tokens'] for r in responses),
            reasoning_tokens=sum(r.get('reasoning_tokens',0) for r in responses),
            tool_seconds=sum(r.get('seconds',0) for r in op_rows),
            fallback=bool(op_rows and op_rows[-1]['status']!='APPLIED'),
            seconds=time.monotonic()-started,gold_exposed=False,protocol=VERSION)
        result['locked_sha256']=fingerprint(result)
        self.events.append('MATH_ANSWER_LOCKED',result,time.time())
        return result

class MathFailureEvidenceStore:
    """Only terminal, host-scored Discovery events; never expose expected answers."""
    def __init__(self,path,score_journal):
        self.events=EvidenceStore(path);self.scores=EvidenceStore(score_journal)

    def record(self, task, locked, verdict, *, role, origin, at):
        if role!='Discovery':raise PermissionError('only Discovery may feed this frozen learner')
        if not any(r['kind']=='MATH_PRIVATE_SCORE' and r['payload']==verdict for r in self.scores.records()):raise PermissionError('actual terminal score receipt required')
        if fingerprint({k:v for k,v in locked.items() if k!='locked_sha256'})!=locked['locked_sha256']:raise ValueError('altered trajectory')
        origins={r['origin'] for r in locked['responses']}
        if origins!={origin} or origin not in ('MOCK','DEEPSEEK'):raise PermissionError('solver origin mismatch')
        if verdict.get('episode_id')!=locked['episode_id'] or verdict.get('locked_sha256')!=locked['locked_sha256']:
            raise ValueError('terminal grade not bound to locked answer')
        if verdict['correct'] or not verdict.get('credible_failure',False):return None
        row=dict(task=task.to_dict(),episode_id=locked['episode_id'],sequence=locked['sequence'],
            final_output=locked['final_output'],trajectory=[dict(text=r['text'],usage=r['usage'],finish_reason=r.get('finish_reason','unknown')) for r in locked['responses']],
            outcome='INCORRECT_AFTER_TASK_LOCK',failure_type='STRUCTURE' if not locked['final_output'].strip() else 'INCORRECT',
            tokens=dict(input=locked['input_tokens'],output=locked['output_tokens'],reasoning=locked['reasoning_tokens']),
            model_calls=locked['model_calls'],tool_results=locked['operator_events'],locked_sha256=locked['locked_sha256'],
            origin=origin,available_after_sequence=locked['sequence'],observed_at=at,gold_exposed=False)
        row['event_id']=fingerprint(row)
        if any(r['payload'].get('event_id')==row['event_id'] for r in self.events.records()):return row
        self.events.append('MATH_TERMINAL_FAILURE',row,at);return row

    def bundle(self, *, after_sequence, allow_mock=False, max_events=24):
        rows=[r['payload'] for r in self.events.records() if r['kind']=='MATH_TERMINAL_FAILURE' and r['payload']['available_after_sequence']<after_sequence]
        if any(r['origin']=='MOCK' for r in rows) and not allow_mock:raise PermissionError('Mock evidence cannot enter real induction')
        # Earliest one per original problem, then chronological selection. No labels.
        seen=set();out=[]
        for row in rows:
            key=' '.join(row['task']['problem'].split())
            if key not in seen:seen.add(key);out.append(row)
        return dict(version=VERSION,events=out[:max_events],cutoff_sequence=after_sequence,omitted_event_ids=[r['event_id'] for r in out[max_events:]],gold_exposed=False)


def run_condition_no_gold(benchmark,condition_name,cfg,llm,tasks,output_dir):
    """Explicit entry from code_math.runner; old evaluator/retry path is not called."""
    from code_math.loader import split_math_tasks
    from code_math.private_math_scoring import PrivateMathScorer
    if output_dir is None:raise ValueError('durable output directory required in no_gold mode')
    root=Path(output_dir)/('no_gold_'+benchmark+'_'+condition_name);root.mkdir(parents=True,exist_ok=True)
    public,private=split_math_tasks(tasks)
    scorer=PrivateMathScorer(private,root/'controller.jsonl',root/'private_scores.jsonl')
    policy=NoGoldPolicy(reflection_calls=cfg.get('reflection_calls',1))
    controller=NoGoldMathController(llm,root/'controller.jsonl',policy=policy)
    episodes=[]
    for i,task in enumerate(public):
        result=controller.solve(task,episode_id=f'{condition_name}/{task.task_id}',sequence=i)
        verdict=scorer.score(task,result)
        episodes.append(dict(task_id=task.task_id,passed=verdict['correct'],tokens=result['input_tokens']+result['output_tokens'],model_calls=result['model_calls'],gold_exposed=False,locked_sha256=result['locked_sha256']))
    (root/'episodes.json').write_text(canonical(episodes)+'\n')
    return episodes
