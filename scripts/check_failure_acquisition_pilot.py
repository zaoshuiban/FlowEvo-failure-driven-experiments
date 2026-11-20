"""Seven bounded pilot preflight checks; never enables live transport."""
import copy
import json
from pathlib import Path
import tempfile
from env.humaneval_loader import load_humaneval_tasks
from failure_evo.acquisition_adapters import CodeAdapter
from failure_evo.pilot_data import task_from_manifest
from failure_evo.pilot_runtime import PilotStop, PilotTransport, IsolatedCodeSandbox, write_json
from failure_evo.skill_runtime import bundle_from_cards
from memory.primitive_store import PrimitiveStore
from run_failure_acquisition_pilot import budget, runner, dry_data, set_context, install_mock, trace_of


def rejected(fn):
    try:fn()
    except (ValueError,RuntimeError,PilotStop):return True
    return False


def run_checks(cfg,data,dry_root):
    root=Path(tempfile.mkdtemp(prefix='checks_',dir=cfg['dry_root']))
    b=budget(cfg,root);client=PilotTransport(cfg,root,b,dry=True);install_mock(client)
    box=IsolatedCodeSandbox(image=cfg['image'],budget=b,root=root,timeout_seconds=1)
    checks={}
    loaded=load_humaneval_tasks(dataset_path=cfg['dataset_path'],public_only=True)
    table={t.task_id:t for t in loaded}
    for row in data['tasks']:
        native=table[row['problem_id']];task=task_from_manifest(row)
        assert native.prompt==task.prompt and native.entry_point==task.entry_point
        assert not native.test and not native.canonical_solution and task.metadata['public_training_tests']
        if row['data_role']=='train':
            public=CodeAdapter().public_view(task)
            assert 'canonical_solution' not in public and 'test' not in public
    # A real typed HumanEval signature must retain its allowed prompt imports.
    native_runner=runner(root/'typed_public',cfg,client,box,frozen=True)
    real_task=task_from_manifest(next(r for r in data['tasks'] if r['problem_id']=='HumanEval/0'))
    client.dry_actor=lambda messages:'from __future__ import annotations\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    return False\n'
    set_context(client,box,'public_boundary','HumanEval_0')
    output=native_runner.executor._invoke_generator(native_runner.executor.dynamic_generator,'draft',task=real_task)
    assert 'from typing import List' in output.code
    from eval.verifier import verify_task
    fb=verify_task(real_task,output.code,box)
    assert not fb.passed and fb.metrics['total_test_count']==2
    assert all('NameError' not in r['error'] for r in fb.metrics['test_results'])
    install_mock(client)
    checks['real_loader_and_public_validation_boundary']=True

    dry=json.loads((Path(dry_root)/'Pilot_Result.json').read_text())
    receipts=[json.loads(p.read_text()) for p in (Path(dry_root)/'requests').rglob('receipt.json')]
    assert {r['role'] for r in receipts}=={'actor','teacher'}
    assert dry['budget']['calls']==len(receipts) and not dry['budget']['unknown_or_pending_requests']
    assert dry['budget']['charged_or_reserved_cost_microusd']==0
    forbidden=PilotTransport(cfg,root/'forbidden',b)
    forbidden.context('collect','never_sent')
    checks['both_model_roles_budgeted_and_live_default_blocked']=rejected(lambda:forbidden.generate(instructions='x',input_text='x',settings=None))

    store=PrimitiveStore(Path(dry_root)/'acquired/primitives/registry.json')
    card=store.list_all()[0];assert card.support_count==2
    support=json.loads(next((Path(dry_root)/'acquisition/supports').glob('*/result.json')).read_text())
    assert support['sha256']==card.source_sha256 and support['status']=='SUPPORT_ADMITTED'
    assert card.support_evidence and card.support_evidence[0]['return_use_verified']
    bad=copy.deepcopy(card.support_evidence[0]);bad['sha256']='0'*64
    assert rejected(lambda:store.observe_support(card.primitive_id,bad))
    before=store.get(card.primitive_id).support_count
    store.observe_support(card.primitive_id,card.support_evidence[0])
    assert store.get(card.primitive_id).support_count==before
    checks['same_sha_independent_support_and_dedup']=True

    draft=card.model_dump(mode='json');draft['status']='draft'
    assert rejected(lambda:bundle_from_cards([draft]))
    pack=bundle_from_cards([draft],training_support=(card.primitive_id,card.source_sha256))
    assert pack['entries']
    checks['draft_requires_explicit_training_support_binding']=True

    # Keep both old helpers and source-verified helpers without a new operation contract
    # on their original source-context path. They must not crash new-mode execution.
    r=runner(root/'legacy',cfg,client,box,frozen=True)
    task=task_from_manifest(dry_data()['tasks'][0])
    from core.utils import infer_task_pattern
    old=card.model_copy(deep=True);old.primitive_id='legacy_prompt_helper';old.validation_status='legacy';old.operation_contracts={}
    old.task_pattern=infer_task_pattern(task);old.code_path=str(r.primitive_store.save_code(old.primitive_id,'def ordered(xs):\n    return sorted(xs,key=abs)\n'))
    r.primitive_store.upsert(old)
    ordinary=old.model_copy(deep=True);ordinary.primitive_id='native_success_helper';ordinary.validation_status='source_verified_dependency_checked'
    r.primitive_store.upsert(ordinary)
    client.dry_actor=lambda messages:'def order_values(xs):\n    return sorted(xs,key=abs)\n'
    set_context(client,box,'compatibility','old_and_native')
    result=r.run_episode(task);trace=trace_of(result)
    assert result['passed'] and len([a for a in trace.actions if a.tool_name=='skill_presented'])==2
    assert not trace.actual_skill_calls
    checks['legacy_and_native_success_prompt_reuse_preserved']=True

    call=pack['card_names'][card.primitive_id];module=pack['entries'][call]['module']
    box.context('isolation','read_only_and_network')
    code=f'''from flowevo_skills import {call}
assert {call}([-4,1]) == [1,-4]
try:
    open('/skills/{module}.py','w')
except OSError:
    pass
else:
    raise AssertionError('skill writable')
import os, socket
assert 'DEEPSEEK_API_KEY' not in os.environ
s=socket.socket();s.settimeout(0.2)
try:
    s.connect(('1.1.1.1',443))
except OSError:
    pass
else:
    raise AssertionError('network available')
'''
    ok=box.run(code,module_bundle=pack);assert ok['passed'] and any(e['event']=='returned' for e in ok['skill_events'])
    box.context('isolation','timeout');timed=box.run('while True: pass\n')
    assert timed['timeout'] and not timed['passed']
    checks['isolated_modules_readonly_network_timeout_receipts']=True
    assert set(json.loads(p.read_text())['status'] for p in (Path(dry_root)/'phases').glob('*.json'))=={'complete'}
    assert dry['funnel']['support_passed']==1 and dry['funnel']['admitted']==1 and dry['funnel']['transfer_calls']>=1
    assert not b.snapshot()['unknown_or_pending_requests']
    checks['staged_entry_dry_run_and_cost_consistency']=True
    result=dict(protocol_sha256=cfg['protocol_sha256'],checks=checks,paid_model_requests=0,checks_run_root=str(root),checks_budget=b.snapshot(),dry_run_root=str(dry_root),dry_funnel=dry['funnel'])
    write_json(Path(cfg['reports'])/'Pilot_Preflight_Receipts.json',result)
    return result
