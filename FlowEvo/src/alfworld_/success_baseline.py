"""Audited ALFWorld full_library lifecycle, with an immutable evaluation bank."""
import copy
import fcntl
import random
import time
from decimal import Decimal
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from alfworld_.audited_baseline import AuditedActionClient, classify_trace
from alfworld_.compiler import AlfWorldCompiler
from alfworld_.env import AlfWorldEnv
from alfworld_.executor import AlfWorldExecutor
from alfworld_.generator import AlfWorldGenerator
from alfworld_.param_extractor import ParamExtractor
from alfworld_.run_20task_validation import AUDIT_INTERVAL, HOLDOUT_RATE, HOLDOUT_RNG_SEED
from alfworld_.schemas import AlfWorldAction, AlfWorldTrace
from alfworld_.skill_library import SkillLibrary
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save
from failure_evo.run_health import RunUnhealthy, trusted_usage
from failure_evo.workflow_protocol_v2 import Limits, prepare
from runtime.config import GenerationSettings


class StrictTrainEnv(AlfWorldEnv):
    """Use actual train/ and the ordinary TextWorld interface without expert extras."""
    def __init__(self, data, max_steps=50):
        super().__init__(split='train', alfworld_data=str(data), max_steps=max_steps)

    def _build_config(self):
        config = super()._build_config()
        config['dataset']['data_path'] = str(Path(self.alfworld_data) / 'json_2.1.1/train')
        config['general']['training_method'] = 'dqn'
        config['rl'] = {'training': {'max_nb_steps_per_episode': self.max_steps}}
        return config


class ReplayEnv:
    """Reconstruct an interrupted local episode and verify its durable public prefix."""
    def __init__(self, env, journal, max_steps):
        self.env, self.journal, self.max_steps = env, journal, max_steps
        self.rows = journal.records()
        self.steps = 0
        self.won = False
        self.done = False

    def check(self, index, kind, payload):
        if index < len(self.rows):
            row = self.rows[index]
            if row['kind'] != kind or row['payload'] != payload:
                raise RunUnhealthy('environment replay diverged')
        else:
            self.journal.append(kind, payload, time.time())

    def reset(self):
        task, obs, commands = self.env.reset()
        self.check(0, 'RESET', dict(game=task.game_file, observation=obs, commands=list(commands)))
        return task, obs, commands

    def step(self, action):
        if self.done or self.steps >= self.max_steps:
            raise RunUnhealthy('executor attempted to step beyond the environment boundary')
        index = self.steps + 1
        if index < len(self.rows) and self.rows[index]['payload']['action'] != action:
            raise RunUnhealthy('environment replay action diverged')
        result = self.env.step(action)
        self.steps += 1
        self.won, self.done = result.won, result.done
        self.check(index, 'STEP', dict(action=action, observation=result.observation,
                                       score=result.score, done=result.done, won=result.won,
                                       commands=list(result.admissible_commands)))
        return result


class BaselineClient(AuditedActionClient):
    """Retain native generator settings and recover a settled raw response receipt."""
    problem = None

    def generate(self, *, instructions, input_text, settings):
        try:
            key = f'{self.request_prefix}{self.episode}/{self.step}'
            rows = [r for r in self.events.records() if r['payload'].get('request_id') == key]
            raw = [r['payload']['response'] for r in rows if r['kind'] == 'RAW_RESPONSE']
            if raw and not any(r['kind'] == 'ACTION_RESPONSE' for r in rows):
                self.health()
                wire = prepare([dict(role='system', content=instructions), dict(role='user', content=input_text)],
                               limits=Limits(input_token_upper=self.config['input_upper'],
                                             output_tokens=settings.max_output_tokens),
                               temperature=settings.temperature)
                state = self.budget.request_state(key)
                if (len(raw) != 1 or not state or state['status'] != 'settled'
                        or state['request_hash'] != wire.sha256):
                    raise RunUnhealthy('raw response cannot be safely reconciled')
                usage = trusted_usage(raw[0])
                choice = raw[0]['choices'][0]
                content = choice['message']['content']
                if (not usage or state['settlement'].get('tokens') != usage['total_tokens']
                        or usage['input_tokens'] > wire.input_upper or usage['output_tokens'] > wire.output_upper
                        or raw[0]['model'] != self.config['model'] or choice['finish_reason'] != 'stop'
                        or not isinstance(content, str) or not content.strip()):
                    raise RunUnhealthy('invalid or incomplete recorded model delivery')
                result = dict(text=content, usage=raw[0]['usage'], model=raw[0]['model'], finish_reason='stop')
                self.events.append('ACTION_RESPONSE', dict(request_id=key, wire_sha256=wire.sha256,
                                                           result=result), time.time())
            result = super().generate(instructions=instructions, input_text=input_text, settings=settings)
            if not result.text.strip():
                raise RunUnhealthy('empty model delivery')
            return result
        except Exception as exc:
            self.problem = exc
            raise


def route(library, task, observation, commands, holdout):
    layers = library.retrieve(task.task_type)
    if holdout:
        layers.update(exemplar=None, insight=None)
    template = layers['template']
    layers['best_layer'] = 1 if template else 2 if layers['exemplar'] else 3 if layers['insight'] else None
    bindings = None
    if template and task.task_type != 'pick_two_obj_and_place':
        bindings = ParamExtractor().extract(task.task_type, task.goal, observation, commands)
    return layers, bindings


def draw_holdout(library, task_type, rng):
    layers = library.retrieve(task_type)
    return bool((layers['exemplar'] or layers['insight']) and rng.random() < HOLDOUT_RATE)


def update_library(library, trace, selected, holdout, compiler, sequence):
    template_id = selected['template']
    if template_id:
        library.record_template_usage(template_id, trace.success)
    if holdout:
        library.record_unguided(trace.task_type, trace.success)
    elif trace.planning_mode in ('exemplar_guided', 'insight_guided',
                                 'direct_then_exemplar', 'direct_then_insight'):
        library.record_guided(trace.task_type, trace.success)
    produced = {}
    if trace.success:
        result = compiler.compile(trace)
        if result.template is not None:
            produced['L1'] = dict(id=result.template.template_id, admitted=library.add_template(result.template))
        if result.exemplar is not None:
            library.add_exemplar(result.exemplar)
            produced['L2'] = dict(id=result.exemplar.exemplar_id, admitted=True)
    had_insight = library.retrieve(trace.task_type)['insight'] is not None
    # A suppressed insight can still exist, so check storage when masked.
    had_insight = had_insight or trace.task_type in library.to_dict()['insights']
    library.record_trace_stats(trace)
    if trace.task_type in library.to_dict()['insights']:
        produced['L3'] = dict(created=not had_insight, refreshed=had_insight)
    audit = library.periodic_audit() if sequence % AUDIT_INTERVAL == 0 else {}
    return produced, audit


def _rng(state):
    rng = random.Random(HOLDOUT_RNG_SEED)
    if state is not None:
        rng.setstate((state[0], tuple(state[1]), state[2]))
    return rng


def solve(root, cfg, row, library, holdout, action, env_factory):
    path = str(Path(cfg['data_root']) / row['game'])
    native = env_factory(cfg['data_root'], cfg['max_steps'])
    try:
        native.initialize(frozen_game_files=[path])
        env = ReplayEnv(native, EvidenceStore(root/'environment.jsonl'), cfg['max_steps'])
        task, obs, commands = env.reset()
        if task.game_file != path or task.task_type != row['task_type']:
            raise RunUnhealthy('game identity mismatch')
        task.task_id = row['task_id']
        available = library.retrieve(task.task_type)
        retrieved = [name for name in ('template','exemplar','insight') if available[name] is not None]
        layers, bindings = route(library, task, obs, commands, holdout)
        selected = dict(template=layers['template'].template_id if layers['template'] else None,
                        exemplar=layers['exemplar'].exemplar_id if layers['exemplar'] else None,
                        insight=layers['insight'] is not None, bound=bindings is not None)
        action.begin(task.task_id)
        generator = AlfWorldGenerator(action, GenerationSettings(temperature=0, max_output_tokens=cfg['output_tokens']))
        trace = AlfWorldExecutor(env, generator, max_steps=cfg['max_steps']).run(
            task, obs, commands, skill_library_result=layers, skill_bindings=bindings)
        if action.problem:
            raise action.problem
        action.health()
        if env.steps + 1 < len(env.rows) or trace.success != env.won or trace.total_steps != env.steps:
            raise RunUnhealthy('executor result differs from environment receipts')
        records = action.events.records()
        responded = {r['payload']['request_id'] for r in records if r['kind'] == 'ACTION_RESPONSE'}
        raw = [r['payload']['wire'] for r in records if r['kind'] == 'ACTION_REQUEST'
               and r['payload']['request_id'] in responded]
        l2 = layers['exemplar'].to_prompt_text() if layers['exemplar'] else ''
        l3 = layers['insight'].to_prompt_text() if layers['insight'] else ''
        use = dict(L1_actions=trace.total_steps-trace.llm_call_count if trace.direct_use_count else 0,
                   L2_requests=sum(bool(l2 and l2 in w['messages'][-1]['content']) for w in raw),
                   L3_requests=sum(bool(l3 and l3 in w['messages'][0]['content']) for w in raw),
                   fallback=trace.planning_mode.startswith('direct_then_'))
        return dict(trace=asdict(trace), retrieved=retrieved, selected=selected, use=use, status=classify_trace(trace))
    finally:
        native.close()


def run_stream(root, cfg, budget, *, sender=None, env_factory=StrictTrainEnv, fault=None, pause_after=None):
    """Called under the CLI run lock. No failure compiler or registry is used."""
    journal = EvidenceStore(root/'episodes.jsonl')
    rows = journal.records()
    for row in rows:
        if row['payload']['protocol_sha256'] != fingerprint(cfg):
            raise RunUnhealthy('checkpoint protocol differs')
    committed = [r['payload'] for r in rows if r['kind'] == 'EPISODE_COMMITTED']
    if [e['task_id'] for e in committed] != [r['task_id'] for r in cfg['tasks'][:len(committed)]]:
        raise RunUnhealthy('committed episode order differs')
    all_online = cfg['online'] == len(cfg['tasks'])
    if all_online:
        for entry in committed:
            publish_online_checkpoint(root, cfg, entry)
    library = SkillLibrary.from_dict(committed[-1]['library']) if committed else SkillLibrary()
    rng = _rng(committed[-1]['rng'] if committed else None)
    freezes = [r['payload'] for r in rows if r['kind'] == 'BANK_FROZEN']
    frozen = freezes[0] if freezes else None
    if len(freezes) > 1 or (frozen and (all_online or frozen['library_sha256'] != fingerprint(library.to_dict()))):
        raise RunUnhealthy('frozen bank drift')
    if frozen:
        if frozen.get('evaluation_holdout') is not False:
            raise RunUnhealthy('unsupported frozen evaluation holdout policy')
        rng = _rng(frozen['rng'])
        save(root/'frozen_bank.json', frozen)
    for seq, row in enumerate(cfg['tasks'][len(committed):], len(committed)+1):
        online = seq <= cfg['online']
        if not online and frozen is None:
            state = library.to_dict()
            frozen = dict(protocol_sha256=fingerprint(cfg), library=state,
                          library_sha256=fingerprint(state), evaluation_holdout=False, rng=rng.getstate())
            journal.append('BANK_FROZEN', frozen, time.time())
            save(root/'frozen_bank.json', frozen)
        before = fingerprint(library.to_dict())
        working = SkillLibrary.from_dict(copy.deepcopy(library.to_dict()))
        if online:
            working.advance_episode()
        holdout = draw_holdout(working, row['task_type'], rng) if online else False
        path = root/'episodes'/row['task_id']
        path.mkdir(parents=True, exist_ok=True)
        action = BaselineClient(path/'action', budget, cfg, sender=sender, request_prefix='action/')
        compilation = BaselineClient(path/'compile', budget, dict(cfg, output_tokens=cfg['compiler_output_tokens']),
                                     sender=sender, request_prefix='compile/')
        identity = dict(task_id=row['task_id'], seq=seq, before=before, holdout=holdout,
                        protocol_sha256=fingerprint(cfg))
        started = started_at(path, identity)
        try:
            action.health()
            compilation.health()
            lock = path/'locked.json'
            if lock.exists():
                outcome = read(lock)
                if outcome['identity'] != identity:
                    raise RunUnhealthy('locked episode identity differs')
            else:
                outcome = solve(path, cfg, row, working, holdout, action, env_factory)
                outcome['identity'] = identity
                save(lock, outcome)
            if fault:
                fault('after_lock', seq)
            produced, audit = {}, {}
            if online:
                trace = AlfWorldTrace(**dict(outcome['trace'], actions=[AlfWorldAction(**x) for x in outcome['trace']['actions']]))
                compilation.begin(row['task_id'])
                produced, audit = update_library(working, trace, outcome['selected'], holdout,
                                                 AlfWorldCompiler(compilation), seq)
                if compilation.problem:
                    raise compilation.problem
                compilation.health()
            state = working.to_dict()
            if not online and fingerprint(state) != before:
                raise RunUnhealthy('evaluation mutated the frozen bank')
            if fault:
                fault('before_commit', seq)
            payload = dict(identity, phase='online' if online else 'evaluation', outcome=outcome,
                           produced=produced, audit=audit, library=state,
                           compile_calls=sum(r['kind'] == 'ACTION_RESPONSE' for r in compilation.events.records()),
                           library_sha256=fingerprint(state), rng=rng.getstate(),
                           elapsed_seconds=time.time()-started,
                           snapshot=working.snapshot())
            journal.append('EPISODE_COMMITTED', payload, time.time())
            library = working
            committed.append(payload)
            if all_online:
                publish_online_checkpoint(root, cfg, payload)
        except Exception as exc:
            save(root/'STOP.json', dict(identity, status='INCOMPLETE', error_class=type(exc).__name__,
                                        reason=str(exc)[:240]))
            raise
        print(f"{seq}/{len(cfg['tasks'])} {payload['phase']} {outcome['status']} "
              f"{outcome['trace']['planning_mode']}", flush=True)
        if pause_after == seq:
            save(root/'pause.json', dict(protocol_sha256=fingerprint(cfg), sequence=seq,
                                         calls=budget.calls, library_sha256=payload['library_sha256']))
            break
    summary = summarize_run(root, cfg, committed, budget)
    save(root/'summary.json', summary)
    return summary


def publish_online_checkpoint(root, cfg, entry):
    """Materialize the committed bank; never change learning or consume RNG."""
    seq = entry['seq']
    final = seq == len(cfg['tasks'])
    if seq % 20 and not final:
        return
    receipt = {k:entry[k] for k in ('seq','protocol_sha256','library','library_sha256','rng','snapshot')}
    receipt['committed_payload_sha256'] = fingerprint(entry)
    paths = [root/'checkpoints'/f'{seq:03d}.json']
    if final:
        paths.append(root/'final_bank.json')
    for path in paths:
        if path.exists():
            if fingerprint(read(path)) != fingerprint(receipt):
                raise RunUnhealthy('materialized bank differs from committed checkpoint')
        else:
            save(path, receipt)


def started_at(path, identity):
    marker = path/'started.json'
    if not marker.exists():
        save(marker, dict(identity=identity, at=time.time()))
    value = read(marker)
    if value['identity'] != identity:
        raise RunUnhealthy('start receipt differs')
    return value['at']


def summarize_run(root, cfg, committed, budget):
    phases = {}
    results = []
    cumulative = 0
    for entry in committed:
        t = entry['outcome']['trace']
        cumulative += t['success']
        results.append(dict(task_id=entry['task_id'], sequence=entry['seq'], task_type=t['task_type'],
                            cumulative_success_rate=cumulative/entry['seq'],
                            phase=entry['phase'], status=entry['outcome']['status'],
                            success=t['success'], steps=t['total_steps'], action_tokens=t['llm_total_tokens_total'],
                            action_calls=t['llm_call_count'], compile_calls=entry.get('compile_calls',0),
                            route=t['planning_mode'], holdout=entry['holdout'], use=entry['outcome']['use'],
                            retrieved=entry['outcome']['retrieved'], selected=entry['outcome']['selected'],
                            produced=entry['produced'], audit=entry['audit'],
                            injection_suppressed=entry['library']['injection_suppressed'],
                            library_sha256=entry['library_sha256'], snapshot=entry['snapshot'],
                            elapsed_seconds=entry['elapsed_seconds']))
    for phase in ('online', 'evaluation', 'total'):
        selected = [r for r in results if phase == 'total' or r['phase'] == phase]
        phases[phase] = outcome_counts(selected)
    windows = [dict(start=i+1, end=min(i+20,len(results)), **outcome_counts(results[i:i+20]))
               for i in range(0,len(results),20)]
    by_type = {kind:outcome_counts([r for r in results if r['task_type']==kind])
               for kind in sorted({r['task_type'] for r in results})}
    usage = {}
    for channel in ('action', 'compile'):
        totals = Counter()
        for path in root.glob(f'episodes/*/{channel}/requests.jsonl'):
            for event in EvidenceStore(path).records():
                if event['kind'] != 'RAW_RESPONSE':
                    continue
                raw = event['payload']['response']
                measured = trusted_usage(raw)
                totals['responses'] += 1
                if measured:
                    totals.update(measured)
                    u = raw['usage']
                    hit = u.get('prompt_cache_hit_tokens', 0)
                    if type(hit) is not int or not 0 <= hit <= measured['input_tokens']:
                        hit = 0
                        totals['invalid_cache_breakdown'] += 1
                    totals['cache_hit'] += hit
                else:
                    totals['unmetered'] += 1
        usage[channel] = dict(totals)
    rates = cfg.get('reference_rates_per_million')
    estimates = {}
    if rates:
        for channel, totals in usage.items():
            hit = totals.get('cache_hit', 0)
            miss = totals.get('input_tokens', 0)-hit
            output = totals.get('output_tokens', 0)
            estimates[channel] = str(sum(Decimal(rates[k])*v for k,v in
                                         (('hit',hit),('miss',miss),('output',output)))/1000000)
    return dict(reference_offpeak_estimates_usd=estimates,
                total_reference_offpeak_usd=str(sum(map(Decimal,estimates.values()))) if rates else None,
                actual_invoice_usd=None,
                expected_episodes=len(cfg['tasks']), not_committed=len(cfg['tasks'])-len(results),
                protocol_sha256=fingerprint(cfg), status='COMPLETED' if len(results)==len(cfg['tasks']) else 'PARTIAL',
                phases=phases, windows=windows, by_type=by_type, results=results, provider_usage=usage, budget=budget.snapshot())

def outcome_counts(rows):
    count = len(rows)
    successes = sum(r['success'] for r in rows)
    return dict(completed=count, successes=successes, success_rate=successes/count if count else None,
                mean_steps=sum(r['steps'] for r in rows)/count if count else None,
                mean_model_calls=sum(r['action_calls']+r['compile_calls'] for r in rows)/count if count else None,
                mean_action_tokens=sum(r['action_tokens'] for r in rows)/count if count else None,
                outcomes=dict(Counter(r['status'] for r in rows)),
                modes=dict(Counter(r['route'] for r in rows)),
                uses={k:sum(r['use'][k] for r in rows) for k in ('L1_actions','L2_requests','L3_requests','fallback')},
                skill_generation={k:sum(k in r['produced'] for r in rows) for k in ('L1','L2','L3')},
                skill_admission={k:sum(bool(r['produced'].get(k,{}).get(field)) for r in rows)
                                 for k,field in (('L1','admitted'),('L2','admitted'),('L3','created'))},
                retrievals={k:sum(k in r['retrieved'] for r in rows) for k in ('template','exemplar','insight')},
                successes_with_skill=sum(r['success'] and any(r['use'][k] for k in ('L1_actions','L2_requests','L3_requests')) for r in rows),
                failures_with_skill=sum(not r['success'] and any(r['use'][k] for k in ('L1_actions','L2_requests','L3_requests')) for r in rows))
