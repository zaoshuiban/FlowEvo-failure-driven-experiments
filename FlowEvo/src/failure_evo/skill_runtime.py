"""Frozen executable helper bundles for the native code executor (opt-in).

This is provenance instrumentation in the native subprocess, not a security
boundary against adversarial Python. No model or task-solving logic lives here.
"""
import ast
import builtins
import hashlib
import json
import re
import symtable
import sys
from pathlib import Path


def sha(source):
    return hashlib.sha256(source.encode()).hexdigest()


def logger_identity():
    return {'version': 'trusted-io-event-log-v2',
            'runtime_source_sha256': sha(Path(__file__).read_text())}


def check_source(source):
    tree = ast.parse(source)
    allowed = (ast.FunctionDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.ClassDef)
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if not isinstance(node, allowed):
            raise ValueError('UNSUPPORTED_TOP_LEVEL')
        if isinstance(node, ast.ClassDef):
            if node.name != 'Solution' or node.bases or node.keywords or node.decorator_list:
                raise ValueError('UNSUPPORTED_CLASS')
            if any(not isinstance(n, (ast.FunctionDef, ast.Pass)) and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in node.body):
                raise ValueError('UNSUPPORTED_CLASS_BODY')
            if any(isinstance(n, ast.FunctionDef) and n.name.startswith('__') for n in node.body):
                raise ValueError('UNSUPPORTED_CUSTOM_CONSTRUCTOR')
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
            if any(m.split('.')[0] not in set(sys.stdlib_module_names) | {'flowevo_skills'} for m in modules):
                raise ValueError('UNSUPPORTED_EXTERNAL_DEPENDENCY')
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            ast.literal_eval(node.value)  # only literal module constants
    table = symtable.symtable(source, '<skill>', 'exec')
    bound = {s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
    def visit(t):
        for s in t.get_symbols():
            if s.is_referenced() and s.is_global() and s.get_name() not in bound | set(dir(builtins)):
                raise ValueError('UNBOUND_FREE_NAME:' + s.get_name())
        for child in t.get_children():
            visit(child)
    visit(table)
    from compiler.gatekeeper import GateKeeper
    ok, why = GateKeeper(None)._static_safety_scan(source)
    if not ok:
        raise ValueError(why)


def validate_bundle(bundle):
    for name, item in bundle.get('modules', {}).items():
        if not re.fullmatch(r'_frozen_[a-f0-9]{64}', name) or sha(item['source']) != item['sha256'] or name != '_frozen_' + item['sha256']:
            raise ValueError('DEPENDENCY_HASH_MISMATCH')
    for name, entry in bundle.get('entries', {}).items():
        if not name.isidentifier() or not entry['entry'].isidentifier():
            raise ValueError('INVALID_BINDING')
        module = bundle.get('modules', {}).get(entry['module'])
        if module is None or module['sha256'] != entry['sha256']:
            raise ValueError('DEPENDENCY_MISSING_OR_CHANGED')


def bundle_from_cards(cards, *, training_support=None, development_permission=None):
    bundle = {'modules': {}, 'entries': {}, 'card_names': {}}
    def merge(other):
        validate_bundle(other)
        for field in bundle:
            for key, val in other.get(field, {}).items():
                if key in bundle[field] and bundle[field][key] != val:
                    raise ValueError('DEPENDENCY_BINDING_CONFLICT')
                bundle[field][key] = val
    for card in cards:
        development_allowed = bool(development_permission
            and development_permission.get('scope') == 'development_diagnostic'
            and development_permission.get('allowed', {}).get(card['primitive_id']) == card.get('source_sha256'))
        draft_allowed = card['status'] == 'draft' and (development_allowed or training_support == (card['primitive_id'], card.get('source_sha256')))
        if (card['status'] != 'active' and not draft_allowed) or card.get('validation_status') != 'source_verified_dependency_checked':
            raise ValueError('EXECUTABLE_SKILL_NOT_VALIDATED')
        source = Path(card['code_path']).read_text()
        if not card.get('source_sha256') or sha(source) != card['source_sha256']:
            raise ValueError('SKILL_HASH_MISMATCH')
        merge(card.get('executable_dependencies', {}))
        name = 'op_' + sha(card['primitive_id'])[:16]
        module = '_frozen_' + sha(source)
        bundle['modules'][module] = dict(source=source, sha256=sha(source))
        bundle['entries'][name] = dict(module=module, entry=card['helper_name'], skill_id=card['primitive_id'], version=sha(source), sha256=sha(source), contract=card.get('operation_contracts',{}).get(card['helper_name'],{}))
        bundle['card_names'][card['primitive_id']] = name
    validate_bundle(bundle)
    return bundle


def materialize(bundle, root, *, event_path=None):
    validate_bundle(bundle)
    for name, item in bundle.get('modules', {}).items():
        (root / (name + '.py')).write_text(item['source'])
    events = Path(event_path) if event_path else root / 'skill_events.jsonl'
    source = '''import importlib, json, time
from io import open as _trusted_event_open
LOGGER_IDENTITY = %r
EVENTS = %r
ENTRIES = %r
def _event(name, event, **extra):
    row = dict(ENTRIES[name], call_name=name, event=event, at=time.time(), logger_identity=LOGGER_IDENTITY, **extra)
    try:
        with _trusted_event_open(EVENTS, 'a') as f: f.write(json.dumps(row) + '\\n')
    except Exception as exc:
        try:
            with _trusted_event_open('/tmp/flowevo_call_log_error', 'w') as f: f.write(type(exc).__name__)
        except Exception:
            pass
        raise RuntimeError('FLOWEVO_CALL_LOG_ERROR') from exc
def _bind(name):
    def invoke(*args, **kwargs):
        _event(name, 'selected')
        try:
            e = ENTRIES[name]
            operation = getattr(importlib.import_module(e['module']), e['entry'])
            _event(name, 'started', argument_types=[type(x).__name__ for x in args], keyword_types={k:type(v).__name__ for k,v in kwargs.items()}, arguments_preview=repr((args,kwargs))[:2048])
            value = operation(*args, **kwargs)
            _event(name, 'returned', result_type=type(value).__name__, result_preview=repr(value)[:4096], preview_truncated=len(repr(value))>4096)
            return None if e.get('ablate_return') else value
        except BaseException as exc:
            _event(name, 'error', error_type=type(exc).__name__)
            raise
    return invoke
for _name in ENTRIES: globals()[_name] = _bind(_name)
''' % (logger_identity(), str(events), bundle.get('entries', {}))
    (root / 'flowevo_skills.py').write_text(source)
    return events
