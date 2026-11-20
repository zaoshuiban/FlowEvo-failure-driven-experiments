"""Read-only closeout audit; standard library only, no experiment imports.

Reads persisted artifacts without starting a model, simulator, container, budget
object, or lock. Run after execution stops. Optional output is created exclusively.
"""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / 'runs/scienceworld_bounded_learning_20261118_01'


def read(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_context(case, steps, limit):
    return dict(goal=case['goal'], observation=(steps[-1] if steps else case['initial'])['observation'],
        action_templates=case['templates'], remaining_steps=limit-len(steps), state={},
        history=[dict(action='[initial observation; zero agent actions]', observation=case['initial']['observation'])]
        + [dict(action=s['action'], observation=s['response']) for s in steps])


def expected_anchor(steps, limit):
    connected = False
    for n, step in enumerate(steps, 1):
        connected |= step['action'].lower().startswith('connect ')
        counts = Counter((s['action'], s['response']) for s in steps[max(0, n-6):n]
                         if s['action'].lower().startswith(('connect ', 'disconnect ', 'activate ', 'deactivate ')))
        if connected and not step['done'] and n <= limit-12 and counts and max(counts.values()) >= 3:
            return n, 'NATURAL_REPETITION_TRIGGER'
    for n, step in enumerate(steps, 1):
        if (step['action'].lower().startswith('connect ') and not step['done']
                and ' is now connected to ' in step['response']):
            return n, 'CONNECTION_PROGRESS_CONTROL'
    return None, 'CONNECTION_PROGRESS_CONTROL'


def cup_render_key(text):
    """Audit rejection classification only; never used to accept a checkpoint."""
    cup = r'a wood cup \(containing (?:red|yellow|blue) paint\)'
    text = re.sub(r'(?:\t'+cup+r'\n)+',
                  lambda m: ''.join(sorted(m[0].splitlines(keepends=True))), text)
    return re.sub(cup+r'(?:, '+cup+r')+',
                  lambda m: ', '.join(sorted(re.findall(cup, m[0]))), text)


class Audit:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.checks = []
        self.summary = {}

    def check(self, name, condition, detail=None):
        self.checks.append(dict(check=name, passed=bool(condition), detail=detail))

    def chain(self, filename):
        path = self.root / filename
        raw = path.read_bytes()
        self.check(filename + ': complete final record', not raw or raw.endswith(b'\n'))
        rows, previous = [], '0'*64
        for number, line in enumerate(raw.splitlines(), 1):
            row = json.loads(line)
            body = {k:v for k,v in row.items() if k != 'record_hash'}
            self.check(f'{filename}: hash chain {number}',
                       row['previous_hash'] == previous and digest(body) == row['record_hash'])
            self.check(f'{filename}: monotonic timestamp {number}', not rows or row['at'] >= rows[-1]['at'])
            rows.append(row)
            previous = row['record_hash']
        return rows

    def audit(self):
        root = self.root
        p = read(root/'protocol.json')
        limit = p['action_limit']
        self.summary['protocol_sha256'] = digest(p)
        self.check('bounded authorized task', p['task'] == 'power-component' and p['simplifications'] == ''
                   and limit == 60 and p['learning_calls'] <= 3)
        for filename, expected in p['files'].items():
            self.check('frozen file: '+filename, Path(filename).is_file() and sha(filename) == expected)
        self.check('frozen Worker source', sha(p['worker']['worker_script']) == p['worker']['worker_sha256'])
        self.check('initial preview', sha(root/'Initial_Native_Request_Preview.json') == p['initial_preview_sha256'])
        source = next(Path(x) for x in p['files'] if x.endswith('/run_scienceworld_bounded_learning.py'))
        literals = {}
        for node in ast.parse(source.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ('NATIVE_PROMPT', 'REPLAN_PROMPT', 'SOURCE_CONTRACT'):
                    literals[node.targets[0].id] = ast.literal_eval(node.value)
        self.check('frozen prompt literals', digest([literals[k] for k in
                   ('NATIVE_PROMPT', 'REPLAN_PROMPT', 'SOURCE_CONTRACT')]) == p['prompt_sha256'])
        split_sets = [set(p['splits'][k]) for k in ('train', 'dev', 'test')]
        self.check('disjoint official splits', all(not split_sets[i] & split_sets[j]
                   for i in range(3) for j in range(i+1, 3)))
        self.check('fixed screening and test lists', p['screening_order'] == sorted(p['splits']['train'])
                   and len(p['screening_order']) <= 10 and p['test_variations'] == p['splits']['test'])

        ledger = self.chain('budget.jsonl')
        self.chain('events.jsonl')
        self.check('ledger protocol binding', bool(ledger) and ledger[0]['kind'] == 'RUN_OPENED'
                   and ledger[0]['payload']['config']['protocol_hash'] == digest(p))
        requests = {}
        for row in ledger:
            kind, value = row['kind'], row['payload']
            ident = value.get('request_id')
            if kind == 'RESERVED':
                self.check('single reservation: '+ident, ident not in requests)
                requests[ident] = dict(value, status='reserved', reserved_at=row['at'], sends=[])
            elif ident in requests:
                item = requests[ident]
                if kind == 'SETTLED': item.update(status='settled', settlement=value)
                elif kind == 'UNKNOWN': item['status'] = 'unknown'
                elif kind == 'NOT_SENT': item['status'] = 'not_sent'
                elif kind == 'NOT_SENT_REOPENED': item['status'] = 'reserved'
                elif kind == 'NETWORK_SEND_STARTED': item['sends'].append(row['at'])
        pending = [k for k,v in requests.items() if v['status'] not in ('settled', 'not_sent')]
        self.requests = requests
        self.check('no unknown or pending requests', not pending, pending)
        self.summary['unknown_or_pending_requests'] = pending
        self.summary['not_sent_requests'] = [k for k,v in requests.items() if v['status'] == 'not_sent']
        self.check('all ledger activity within original deadline',
                   all(r['at'] <= ledger[0]['payload']['deadline'] for r in ledger))
        totals = dict(calls=0, tools=0, tokens=0, cost_microusd=0, tool_milliseconds=0)
        for ident, item in requests.items():
            self.check('at most one POST: '+ident, len(item['sends']) <= 1)
            if item['status'] == 'not_sent':
                self.check('NOT_SENT has no send: '+ident, not item['sends'])
                continue
            settled = item.get('settlement', {})
            totals['calls'] += item['kind'] == 'model'
            totals['tools'] += item['kind'] == 'tool'
            totals['tokens'] += settled.get('tokens', item['token_upper'])
            totals['cost_microusd'] += settled.get('cost_microusd', item['cost_upper_microusd'])
            totals['tool_milliseconds'] += settled.get('tool_milliseconds', item['tool_milliseconds_upper'])
        for key, cap in (('calls','max_calls'), ('tools','max_tools'), ('tokens','max_tokens'),
                         ('cost_microusd','max_cost_microusd'), ('tool_milliseconds','max_tool_milliseconds')):
            self.check('budget ceiling: '+key, totals[key] <= p[cap])
        self.summary['charged_or_reserved_usage'] = totals
        self.audit_amendment(p, ledger)

        logical = {}
        for path in sorted((root/'requests').rglob('logical_call.json')):
            entry = read(path)
            ident = entry['request_id']
            self.check('logical identity: '+ident, str(path.parent.relative_to(root/'requests')) == ident
                       and ident not in logical)
            wire = read(path.parent/'request.private.json')
            self.check('logical wire hash: '+ident, digest(wire) == entry['wire_sha256'])
            self.check('fixed model: '+ident, wire['model'] == p['model'] and wire['temperature'] == 0)
            response = read(path.parent/'response.json')
            self.check('provider model: '+ident, response.get('model') == p['model'])
            if (path.parent/'cache.json').exists():
                cache = read(path.parent/'cache.json')
                original = root/'requests'/cache['source']
                self.check('exact cache provenance: '+ident, cache['wire_sha256'] == digest(wire)
                           and read(original/'request.private.json') == wire
                           and read(original/'response.json') == response)
            else:
                item = requests.get(ident, {})
                usage = response.get('usage', {})
                self.check('response ledger binding: '+ident, item.get('kind') == 'model'
                           and item.get('request_hash') == digest(wire) and item.get('status') == 'settled'
                           and item.get('settlement', {}).get('tokens') == usage.get('total_tokens'))
            logical[ident] = dict(path=path, wire=wire, response=response)
        learning = {k:v for k,v in logical.items() if k.startswith('learning/')}
        testing = {k:v for k,v in logical.items() if k.startswith('test/')}
        self.check('at most three learning requests', len(learning) <= min(3, p['learning_calls']))
        self.summary['logical_requests'] = len(logical)
        self.summary['learning_requests'] = len(learning)
        self.summary['cache_hits'] = sum((v['path'].parent/'cache.json').exists() for v in logical.values())

        screening = read(root/'Screening_Result.json')
        rows = screening['rows']
        self.check('screening uses fixed prefix', [r['variation'] for r in rows] == p['screening_order'][:len(rows)])
        self.summary['screening_status'] = screening['status']
        for row in rows:
            base = root/'screening'/f"{row['variation']:02d}"
            result = read(base/'native/result.json')
            self.audit_branch(base/'native', read(base/'case.json'), result, logical, limit)
        if screening['status'] == 'NO_NATURAL_DEVELOPMENT_FAILURE':
            self.check('no-failure stop completes screen', len(rows) == len(p['screening_order']))
            self.check('no-failure stop has no learning or test', not learning and not testing
                       and not (root/'Frozen_Candidate.json').exists())
            self.summary['terminal_status'] = 'NO_NATURAL_DEVELOPMENT_FAILURE'
            return
        self.check('screening ready', screening['status'] == 'READY_TO_LEARN')
        for name in ('development', 'learning_input'):
            self.check(name+' evidence hash', sha(root/(name+'.json')) == screening[name+'_sha256'])
        development = read(root/'development.json')
        material = read(root/'learning_input.json')
        self.check('development limited to train', 1 <= len(development) <= 3
                   and all(x['variation'] in split_sets[0] for x in development))
        expected_episodes = []
        for item in development:
            original = read(root/'screening'/f"{item['variation']:02d}"/'native/result.json')
            self.check('development genuine prefix', item['steps'] == original['steps'][:len(item['steps'])])
            expected_episodes.append(dict(goal=item['goal'], initial_observation=item['initial']['observation'],
                history=public_context(item, original['steps'], limit)['history'],
                won=original['won'], outcome=original['status']))
        expected_material = dict(episodes=expected_episodes,
            includes_real_recovery_suffixes=any(x['won'] for x in expected_episodes),
            checkpoint_contexts=[public_context(x, x['steps'], limit) for x in development])
        self.check('learner material only public recorded evidence', material == expected_material)

        frozen = read(root/'Frozen_Candidate.json')
        freeze_time = datetime.fromisoformat(frozen['at']).timestamp()
        self.check('candidate freeze protocol binding', frozen['protocol_sha256'] == digest(p)
                   and frozen['learning_requests'] == len(learning))
        self.summary['candidate_status'] = frozen['status']
        versions = []
        for ident, entry in learning.items():
            number = int(ident.removeprefix('learning/v'))
            folder = root/'learning'/f'v{number}'
            raw = entry['response']['choices'][0]['message']['content']
            stored = read(folder/'candidate.json')
            self.check('raw candidate response: '+ident, stored['raw_text'] == raw)
            try: original = json.loads(raw)
            except (ValueError, TypeError): original = None
            source_text = original.get('code', '') if isinstance(original, dict) else ''
            if not isinstance(source_text, str): source_text = ''
            self.check('unaltered candidate source: '+ident, (folder/'candidate.py').read_text() == source_text)
            outcome = read(folder/'evaluation.json')
            self.check('candidate source hash: '+ident, outcome['code_sha256'] == sha(folder/'candidate.py'))
            for j, result in enumerate(outcome['rows']):
                branch_directory = folder/f'development_{j}'
                self.check('development evaluation recorded exactly: '+ident,
                           read(branch_directory/'result.json') == result)
                self.audit_branch(branch_directory, development[j], result, logical, limit)
                self.check('development never invokes native fallback: '+ident,
                           result['logical_model_calls'] == 0)
            versions.append(outcome)
            request_payload = json.loads(entry['wire']['messages'][-1]['content'])
            expected_payload = dict(material, iteration=number,
                previous_attempt=read(root/'learning'/f'v{number-1}'/'feedback.json') if number else None)
            self.check('learning request exact evidence projection: '+ident, request_payload == expected_payload)
            self.check('learning before freeze: '+ident, ident in requests
                       and requests[ident]['reserved_at'] <= freeze_time
                       and all(t <= freeze_time for t in requests[ident]['sends']))
        self.check('contiguous learning versions', sorted(x['version'] for x in versions) == list(range(len(versions))))
        eligible = [x for x in versions if x['static_pass']]
        best = max(eligible, key=lambda x:x['rank']) if eligible else None
        self.check('frozen selection follows development rank',
            frozen['version'] == (best['version'] if best else None)
            and frozen['code_sha256'] == (best['code_sha256'] if best else None))
        for ident, entry in testing.items():
            # Real paid requests have durable journal timestamps. Cached decisions
            # have no ledger reservation, so their artifact timestamp is secondary
            # evidence; exact cache sources are verified above.
            item = requests.get(ident)
            after = (item['reserved_at'] >= freeze_time and all(t >= freeze_time for t in item['sends'])) if item else True
            self.check('test request after freeze: '+ident, after and entry['path'].stat().st_mtime >= freeze_time)
        self.summary['timing_evidence'] = 'Durable ledger reservation/send times; filesystem timestamps for logical cache decisions.'
        if frozen['status'] == 'NO_EXECUTABLE_SKILL':
            self.check('no executable skill means no test rollout', not testing and not eligible)
            self.summary['terminal_status'] = 'NO_EXECUTABLE_SKILL'
            return

        independent = read(root/'Independent_Result.json')
        self.check('experiment completion within original deadline',
                   datetime.fromisoformat(independent['completed_at']).timestamp() <= ledger[0]['payload']['deadline'])
        self.check('independent result freeze binding', independent['frozen'] == frozen)
        self.check('all and only fixed test variations', [x['variation'] for x in independent['games']] == p['test_variations'])
        pairs, metric_rows = [], []
        for game in independent['games']:
            base = root/'test'/f"{game['variation']:02d}"
            case = read(base/'case.json')
            baseline = read(base/'native/result.json')
            self.audit_branch(base/'native', case, baseline, logical, limit)
            anchor, group = expected_anchor(baseline['steps'], limit)
            self.check('predefined test anchor: '+str(game['variation']), (game['anchor'], game['group']) == (anchor, group))
            if anchor is None:
                self.check('no checkpoint recorded', read(base/'no_checkpoint.json') == game)
                continue
            checkpoint = read(base/'pair/checkpoint.json')
            self.check('checkpoint genuine baseline prefix', checkpoint == dict(case, steps=baseline['steps'][:anchor]))
            arms = {arm:read(base/'pair'/arm/'result.json') for arm in ('G','R','F')}
            for arm, result in arms.items():
                self.audit_branch(base/'pair'/arm, checkpoint, result, logical, limit)
            expected_start = digest(public_context(checkpoint, checkpoint['steps'], limit))
            self.check('paired identical starts: '+str(game['variation']),
                       all(x['start_sha256'] == expected_start and x['remaining'] == limit-anchor for x in arms.values()))
            self.check('G exactly matches native suffix: '+str(game['variation']), arms['G']['steps'] == baseline['steps'])
            pair = read(base/'pair/paired_result.json')
            expected_pair = dict(variation=game['variation'], group=group, anchor=anchor,
                arms={a:{k:r[k] for k in ('won','status','suffix_steps','logical_model_calls','cache_hits',
                    'worker_calls','policy_actions','policy_errors','start_sha256')} for a,r in arms.items()})
            self.check('paired summary exact', pair == expected_pair)
            pairs.append(pair)
            metric_rows.append(dict(variation=game['variation'], group=group,
                rescue=not arms['G']['won'] and arms['F']['won'], harm=arms['G']['won'] and not arms['F']['won'],
                common_success=arms['G']['won'] and arms['F']['won'],
                calls_saved_if_common=(arms['G']['logical_model_calls']-arms['F']['logical_model_calls'])
                    if arms['G']['won'] and arms['F']['won'] else None,
                actions_saved_if_common=(arms['G']['suffix_steps']-arms['F']['suffix_steps'])
                    if arms['G']['won'] and arms['F']['won'] else None))
        self.check('independent pairs exact', independent['pairs'] == pairs)
        self.summary['paired_outcomes'] = metric_rows
        self.summary['terminal_status'] = 'INDEPENDENT_EVALUATION_COMPLETE'

    def audit_branch(self, directory, case, result, logical, limit):
        ident = str(directory.relative_to(self.root))
        prefix = len(case['steps'])
        self.check('branch start: '+ident, read(directory/'start.json') == public_context(case, case['steps'], limit)
                   and result['start_sha256'] == digest(public_context(case, case['steps'], limit)))
        self.check('branch original budget and prefix: '+ident,
            result['anchor'] == prefix and result['remaining'] == limit-prefix
            and result['steps'][:prefix] == case['steps']
            and result['suffix_steps'] == len(result['steps'])-prefix
            and len(result['steps']) <= limit and len(result['records']) == result['suffix_steps'])
        for n, record in enumerate(result['records'], prefix+1):
            self.check(f'branch step record: {ident}/{n}', record['step'] == n
                and record['feedback'] == result['steps'][n-1]
                and read(directory/'steps'/f'{n:02d}.json') == record)
        own = {k:v for k,v in logical.items() if k.startswith(ident+'/')}
        self.check('branch logical accounting: '+ident, result['logical_model_calls'] == len(own)
                   and result['cache_hits'] == sum((v['path'].parent/'cache.json').exists() for v in own.values()))
        if result['status'] == 'MODEL_FORMAT_ERROR':
            error = read(directory/'format_error.json')
            request = error['request']
            entry = own.get(request['request_id'])
            self.check('format failure preserves paid/cached response: '+ident,
                entry is not None and request['text'] == entry['response']['choices'][0]['message']['content']
                and request['request_id'].endswith(f"/action_{len(result['steps'])+1:02d}"))
            executed_model_actions = sum(r['actor'] == 'MODEL' for r in result['records'])
            self.check('format failure counts unexecuted model decision: '+ident,
                result['logical_model_calls'] == executed_model_actions + 1 + (result['arm'] == 'R'))
            self.summary.setdefault('model_format_errors', []).append(dict(branch=ident,
                suffix_actions=result['suffix_steps'], logical_model_calls=result['logical_model_calls'],
                error=error['error']))
        for request_id, entry in own.items():
            payload = json.loads(entry['wire']['messages'][-1]['content'])
            if request_id.endswith('/plan'):
                expected = public_context(case, case['steps'], limit)
                self.check('one bounded R plan: '+ident, result['arm'] == 'R' and entry['wire']['max_tokens'] == 1024)
            else:
                n = int(request_id.rsplit('action_', 1)[-1])
                expected = public_context(case, result['steps'][:n-1], limit)
                if result['plan']: expected['replanning_note'] = result['plan']
            self.check('public action input exact (no private IDs/oracle): '+request_id, payload == expected)
        tail = result['steps'][-1] if result['steps'] else case['initial']
        self.check('official success semantics: '+ident, result['won'] == bool(tail['done'] and tail['score'] == 100))
        self.check('reset never submitted: '+ident,
                   all(not s['action'].strip().lower().startswith('reset') for s in result['steps']))
        if result['arm'] == 'F':
            if ident.startswith('learning/'):
                code = self.root/'learning'/ident.split('/')[1]/'candidate.py'
            else:
                frozen = read(self.root/'Frozen_Candidate.json')
                code = self.root/'learning'/f"v{frozen['version']}"/'candidate.py'
            receipts = sorted((directory/'workers').glob('*.json'))
            self.check('Worker invocation count: '+ident, len(receipts) == result['worker_calls'])
            state = {}
            for path in receipts:
                receipt = read(path)
                n = int(path.stem)
                expected = public_context(case, result['steps'][:n-1], limit)
                expected['state'] = state
                self.check('Worker public context and unaltered source: '+str(path.relative_to(self.root)),
                           receipt['context_sha256'] == digest(expected) and receipt['code_sha256'] == sha(code))
                account = self.requests.get(receipt['budget_request_id'], {})
                self.check('Worker ledger settlement: '+str(path.relative_to(self.root)),
                           account.get('kind') == 'tool' and account.get('status') == 'settled')
                state = receipt['result'].get('state', {})
            saw_model = False
            for record in result['records']:
                if record['actor'] == 'MODEL': saw_model = True
                else: self.check('no skill reentry: '+ident, not saw_model)

    def audit_amendment(self, protocol, ledger):
        path = self.root/'Runtime_Amendment.json'
        if not path.exists():
            self.check('no unregistered replay adapter log', not (self.root/'replay_attempts.jsonl').exists())
            return
        amendment = read(path)
        amended_at = datetime.fromisoformat(amendment['at']).timestamp()
        deadline = ledger[0]['payload']['deadline']
        opened_at = ledger[0]['at']
        self.check('original four-hour deadline unchanged',
            ledger[0]['payload']['config']['wall_seconds'] == protocol['wall_seconds'] == 14400
            and abs(deadline-opened_at-14400) < 0.01)
        original = next(name for name in protocol['files'] if name.endswith('/run_scienceworld_bounded_learning.py'))
        self.check('amendment preserves original protocol and source',
            amendment['kind'] == 'INFRASTRUCTURE_ONLY_EXACT_REPLAY_RETRY'
            and amendment['original_protocol_sha256'] == digest(protocol)
            and amendment['original_source_sha256'] == protocol['files'][original] == sha(original)
            and amendment['max_replay_attempts'] == 16)
        self.check('resume adapter frozen source hash',
            sha(amendment['resume_script']) == amendment['resume_script_sha256'])
        source = Path(amendment['resume_script']).read_text()
        # This adapter was independently read in full. Its acceptance path compares
        # the unmodified feedback dict after reset and after EVERY prefix action;
        # cup_render_key is reached only after EXACT_REPLAY_REJECTED is logged.
        tree = ast.parse(source)
        maximum = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'MAX_REPLAYS' for t in n.targets))
        self.check('reviewed acceptance uses literal full feedback comparisons', maximum == 16
            and source.count('if actual != expected:') == 2
            and source.index("events.append('EXACT_REPLAY_ACCEPTED'") < source.index('cup_render_key(expected[k])')
            and "deadline=first['payload']['deadline']" in source)
        sends_before = [r for r in ledger if r['kind'] == 'NETWORK_SEND_STARTED' and r['at'] < amended_at]
        self.check('amendment pre-send count', len(sends_before) == amendment['pre_amendment_model_sends'])
        self.check('amendment pre-learning count',
            sum(r['payload']['request_id'].startswith('learning/') for r in sends_before)
            == amendment['pre_amendment_learning_requests'])
        if (self.root/'Frozen_Candidate.json').exists():
            self.check('amendment before candidate freeze',
                       amended_at < datetime.fromisoformat(read(self.root/'Frozen_Candidate.json')['at']).timestamp())

        cases = {}
        for case_path in list(self.root.rglob('case.json')) + list(self.root.rglob('checkpoint.json')):
            case = read(case_path)
            if isinstance(case, dict) and {'variation','goal','templates','initial','steps'} <= set(case):
                cases[digest(case)] = case
        if (self.root/'development.json').exists():
            for case in read(self.root/'development.json'): cases[digest(case)] = case
        rows = self.chain('replay_attempts.jsonl')
        accepted, group, replay_actions, elapsed_ms, max_attempt = [], [], 0, 0, 0
        for number, event in enumerate(rows, 1):
            value = event['payload']
            identity = value['case_sha256']
            self.check(f'replay {number}: known case and original deadline',
                       identity in cases and amended_at <= event['at'] <= deadline)
            case = cases[identity]
            self.check(f'replay {number}: fixed attempt sequence and cap',
                1 <= value['attempt'] <= 16 and value['attempt'] == len(group)+1
                and (not group or group[0]['payload']['case_sha256'] == identity)
                and value['prefix_steps'] == len(case['steps']) and value['variation'] == case['variation'])
            group.append(event)
            replay_actions += value['replay_actions']
            elapsed_ms += value['milliseconds']
            max_attempt = max(max_attempt, value['attempt'])
            if event['kind'] == 'EXACT_REPLAY_REJECTED':
                expected, actual = value['expected'], value['actual']
                differences = [key for key in expected if expected[key] != actual.get(key)]
                stage = 0 if value['stage'] == 'initial' else int(value['stage'].split('/')[1])
                old = case['initial'] if stage == 0 else case['steps'][stage-1]
                self.check(f'replay {number}: only diagnosed paint-cup render-order rejection',
                    expected == old and actual != expected and set(actual) == set(expected)
                    and differences == value['differing_fields'] and bool(differences)
                    and set(differences) <= {'observation','response'}
                    and all(cup_render_key(expected[k]) == cup_render_key(actual[k]) for k in differences)
                    and value['replay_actions'] == stage)
            elif event['kind'] == 'EXACT_REPLAY_ACCEPTED':
                tail = case['steps'][-1] if case['steps'] else case['initial']
                self.check(f'replay {number}: literal final feedback and all-prefix action count',
                    value['final_public_sha256'] == digest(tail)
                    and value['replay_actions'] == len(case['steps']) and value['max_attempts'] == 16
                    and value['comparison'] == 'Every initial/prefix feedback field exactly equal')
                began_at = group[0]['at'] - group[0]['payload']['milliseconds']/1000 - 0.002
                self.check(f'replay {number}: zero API sends during restoration',
                    not any(r['kind'] == 'NETWORK_SEND_STARTED' and began_at <= r['at'] <= event['at'] for r in ledger))
                accepted.append(event)
                group = []
            else:
                self.check(f'replay {number}: registered event kind', False, event['kind'])
        self.check('no unfinished restoration group at closeout', not group)
        starts = sorted((x for x in self.root.rglob('start.json') if x.stat().st_mtime >= amended_at),
                        key=lambda x:x.stat().st_mtime)
        self.check('each resumed branch has one accepted restoration', len(starts) == len(accepted))
        for index, (start, event) in enumerate(zip(starts, accepted)):
            case = cases[event['payload']['case_sha256']]
            start_time = start.stat().st_mtime
            self.check('accepted state before branch: '+str(start.parent.relative_to(self.root)),
                event['at'] <= start_time
                and (index+1 == len(accepted) or start_time < accepted[index+1]['at'])
                and read(start) == public_context(case, case['steps'], protocol['action_limit']))
        self.summary['restoration'] = dict(amendment_sha256=sha(path),
            resume_script_sha256=amendment['resume_script_sha256'], attempts=len(rows), accepted=len(accepted),
            rejected=len(rows)-len(accepted), largest_attempt_count=max_attempt,
            zero_api_replay_actions=replay_actions, zero_api_replay_milliseconds=elapsed_ms,
            original_deadline=deadline,
            evidence_limit='Accepted intermediate actual raw feedback was compared by the hash-frozen reviewed adapter but not duplicated in its journal. Final raw hashes, complete archived prefixes, and every G suffix are independently recomputed. No complete hidden-state snapshot claim.')

    def result(self):
        try:
            self.audit()
        except (OSError, ValueError, KeyError, TypeError, StopIteration, IndexError) as exc:
            self.check('complete readable closeout artifacts', False, type(exc).__name__+': '+str(exc))
            self.summary.setdefault('terminal_status', 'INCOMPLETE_OR_INVALID')
        failed = [x for x in self.checks if not x['passed']]
        return dict(audited_at=datetime.now(timezone.utc).isoformat(), run=str(self.root),
            passed=not failed, checks=len(self.checks), failures=failed, summary=self.summary,
            scope='Persisted evidence only; no simulator replay, model calls, container execution, or semantic proof of strategy.',
            audit_script_sha256=sha(__file__))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = Audit(args.run).result()
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n'
    if args.output:
        with args.output.open('x') as output:
            output.write(text)
    print(text, end='')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
