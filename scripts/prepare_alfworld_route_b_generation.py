"""Route B generation preflight. ONLY Mock calls; no paid-run CLI exists here."""
import argparse
import json
from pathlib import Path
from alfworld_.route_b_compact_projection import validate,decode,encode,INSTRUCTION
from alfworld_.route_b_information import load_cohort,SYSTEM
from alfworld_.recovery_acquisition import RecoveryAdapter,stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import read,sha
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.model_api import configured_api_key
from failure_evo.wire_input_policy import check_wire
from run_alfworld_a4_confirmatory import commit

VERSION='route-b-generation-preflight-v1'
POLICY=dict(version='route-a3-wire-v1',model='deepseek-flash',max_wire_input_bytes=262144,
    max_input_tokens=262400,model_context_tokens=1000000,output_tokens=4096,estimator='UTF8_BYTES_PLUS_256_UPPER')
PROMPT=SYSTEM+'\n'+INSTRUCTION
REVISION=PROMPT+'\nRevise your own previous complete source or delivery using only engineering diagnostics. No environment supervision is supplied. Return complete source or ABSTAIN. Do not infer mathematical or task correctness from static acceptance.'

def make_wire(root,payload,prompt):
    adapter=RecoveryAdapter(root/'provider.jsonl',None,model='deepseek-flash',mock=True,sender=lambda _:None,
        stage='analyze',payload=payload,parser=parse_delivery,protocol=VERSION,analysis_prompt=prompt,
        temperature=0.6,max_wire_input_upper=POLICY['max_input_tokens'],wire_input_policy=POLICY)
    return adapter.preflight(dict(phase='induction',max_tokens=4096,
        discovery=dict(stage='analyze',payload_sha256=fingerprint(payload))))

def prepare(output,inputs):
    if output.exists():raise FileExistsError('new preflight directory required')
    cohort=load_cohort(Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01')
    frozen=validate(read(inputs/'projection.private.json'),cohort)
    output.mkdir(mode=0o700,parents=True)
    jobs=[];measurements={}
    for arm in ('T','S','F'):
        payload=json.loads(frozen['wires'][arm]['messages'][1]['content'])
        assert decode(payload)==frozen['inputs'][arm]
        w=make_wire(output,payload,PROMPT);measurements[arm]=check_wire(w,POLICY)
        for i in range(4):
            name=f'{arm}_candidate_{i}_initial';jobs.append(dict(name=name,arm=arm,slot=i,
                payload_sha256=fingerprint(payload),wire_sha256=fingerprint(w)))
        commit(output/f'{arm}_wire.private.json',w)
        # One full previous source OR unparsed delivery; no duplicated code/raw.
        # 64KiB artifact + 2KiB engineering diagnostic stress. Never trim overflow.
        stress=dict(original_learning_input=frozen['inputs'][arm],parent_version='f'*64,
            previous_source_or_delivery='x'*65536,
            engineering_diagnostics=[dict(path='$.code',code='STATIC_ERROR',message='z'*2048)])
        try:measurements[arm+'_revision_stress']=check_wire(make_wire(output,encode(stress),REVISION),POLICY)
        except ValueError:
            measurements[arm+'_revision_stress']=dict(status='OVER_LIMIT_FAIL_CLOSED')
    # If stress does not fit, no claim of all feedback envelopes fitting.
    plan=dict(version=VERSION,source_packet_sha256=fingerprint(frozen),run_id=output.name,
        model='deepseek-flash',documented_version='DeepSeek-V4.1-Flash-1017',temperature=0.6,
        thinking='disabled',output_tokens=4096,input_policy=POLICY,network_policy=DEFAULT_POLICY,
        jobs=jobs,candidates_per_arm=4,revisions_per_candidate=1,max_calls=24,
        max_tokens=24*(262400+4096),max_cost_microusd=8000000,
        arm_allocations={a:dict(max_calls=8,max_tokens=8*(262400+4096),max_cost_microusd=2666666) for a in ('T','S','F')},
        reservation_rate_microusd_per_million=1200000,
        peak_quote=dict(input_usd_per_million=0.30,output_usd_per_million=1.20,
            date='2026-11-16',source='https://api-docs.deepseek.com/quick_start/pricing/'),
        max_peak_price_estimate_usd=(24*262400*.30+24*4096*1.20)/1000000,
        max_uniform_rate_reservation_usd=24*(262400+4096)*1.20/1000000,
        revision_trigger='DELIVERY_OR_STATIC_REJECTION_ONLY',feedback='OWN_SOURCE_AND_ENGINEERING_DIAGNOSTICS_ONLY',
        overlarge_revision='STOP_CANDIDATE_INPUT_LIMIT_NO_TRUNCATION',
        abstention_duplicates='PRESERVE_NO_REPLACEMENT_NO_EXTRA_REQUEST',
        selection='FREEZE_ALL_NO_WINNER_UNTIL_COMMON_DEVELOPMENT_LABELS_AND_SELECTION_RULES_FROZEN',
        evaluation_scope='GENERATION_AND_STATIC_ONLY_NO_ENVIRONMENT_MODEL_CALLS',
        worker_calls=0,environment_steps=0,measurements=measurements,
        credential_present=bool(configured_api_key()),credential_validated_with_provider=False,
        model_dictionary_comprehension='UNTESTED_WITH_REAL_MODEL',paid_authorization=False)
    commit(output/'protocol.json',plan)
    # Existing durable compiler/sender/ledger path, not just a constructed wire.
    accounts={a:PersistentBudget(output/f'{a}_mock_budget.jsonl',run_id='engineering:'+output.name+':'+a,
        protocol_hash=fingerprint(plan),max_calls=8,max_tokens=plan['arm_allocations'][a]['max_tokens'],max_tools=0,
        max_cost_microusd=2666666,token_rate_microusd_per_million=1200000,
        tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=1000,wall_seconds=3600)
        for a in ('T','S','F')}
    sent=[]
    fixture_code="import os\ndef environment_operator(c):\n return {'status':'declined','state':{},'reason':'fixture'}"
    def sender(w):
        check_wire(w,POLICY);sent.append(fingerprint(w))
        content=(dict(decision='ABSTAIN',reason='engineering fixture revision') if w['messages'][0]['content']==REVISION else
            dict(decision='PROPOSE',code=fixture_code,description='ENGINEERING_ONLY',applicability='ENGINEERING_ONLY'))
        return dict(id='MOCK-'+str(len(sent)),model='deepseek-flash',usage=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120),
            choices=[dict(message=dict(content=canonical(content)),finish_reason='stop')])
    for job in jobs:
        from failure_evo.run_health import assert_run_healthy
        assert_run_healthy(budgets=list(accounts.values()))
        b=accounts[job['arm']]
        payload=json.loads(read(output/f"{job['arm']}_wire.private.json")['messages'][1]['content'])
        def call():return stage_request(output/'mock',job['name'],'analyze',payload,parse_delivery,b,
            sender=sender,protocol=VERSION,analysis_prompt=PROMPT,temperature=0.6,input_policy=POLICY)
        first=call();before=sha(output/f"{job['arm']}_mock_budget.jsonl");second=call()
        assert first==second and before==sha(output/f"{job['arm']}_mock_budget.jsonl")
        from alfworld_.failure_learning import static_check
        diagnostic=static_check(fixture_code);assert not diagnostic['passed']
        revision=encode(dict(original_learning_input=frozen['inputs'][job['arm']],
            parent_version=fingerprint([job,fixture_code]),previous_source_or_delivery=fixture_code,
            engineering_diagnostics=diagnostic))
        def revise():return stage_request(output/'mock',job['name']+'_revision','analyze',revision,parse_delivery,b,
            sender=sender,protocol=VERSION,analysis_prompt=REVISION,temperature=0.6,input_policy=POLICY)
        repaired=revise();before=sha(output/f"{job['arm']}_mock_budget.jsonl")
        assert revise()==repaired and sha(output/f"{job['arm']}_mock_budget.jsonl")==before
    assert len(sent)==24 and all(b.calls==8 for b in accounts.values())
    # Without a real grant, the same adapter refuses before any real send.
    denied=False
    try:
        RecoveryAdapter(output/'denied.jsonl',b,model='deepseek-flash',stage='analyze',payload={},
            parser=parse_delivery,protocol=VERSION,max_wire_input_upper=POLICY['max_input_tokens'],wire_input_policy=POLICY).preflight({})
    except PermissionError:denied=True
    assert denied
    summary=dict(status='PREFLIGHT_PASSED_AUTHORIZATION_REQUIRED',paid_requests=0,mock_calls=len(sent),
        settled_reentry_no_duplicate_charge=True,unauthorized_real_send_blocked=denied,
        protocol_sha256=fingerprint(plan),credential_present=plan['credential_present'],
        actual_provider_model_and_token_usage='UNOBSERVED',revision_stress=measurements,
        note='Generation-only ceiling; source environment verification requires separate frozen validation plan. No paid authorization created.')
    commit(output/'source_manifest.json',{str(Path(p).resolve()):sha(p) for p in [__file__,
        'FlowEvo/src/alfworld_/recovery_acquisition.py','FlowEvo/src/failure_evo/autonomous_generation.py',
        'FlowEvo/src/failure_evo/compile_queue.py','FlowEvo/src/failure_evo/wire_input_policy.py']})
    return commit(output/'summary.json',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--inputs',type=Path,default=Path('runs/alfworld_route_b_b01_20261116_02'))
    a=p.parse_args();print(canonical(prepare(a.output.resolve(),a.inputs.resolve())))
