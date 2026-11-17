"""Paired A3b extension of the A2/A3 engine; no A4/exposed regression entry."""
import argparse
import fcntl
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from dataclasses import replace
from time import time
import json
import run_alfworld_applicability_multicandidate as B
from alfworld_ import recovery_learning_input as I
from alfworld_.applicability_semantic_feedback import VERSION,instrument,decode_trace,category,paired_feedback
from audit_alfworld_a3b import OLD,card_for,archived_hashes
from alfworld_.applicability_paired_metrics import analyze
from failure_evo.contracts import canonical,fingerprint
from failure_evo.math_stream import read,sha

PROMPT_FILE=B.ROOT/'experiments/route_a3b/A3b_Generation_Prompt.md'

def prompts():
    initial=PROMPT_FILE.read_text()
    return initial,initial+'\nRevise the complete parent source at most once using only your own supplied TRAIN feedback. Candidate reasons are self-reports, not facts. No other branch or validation result is available. Preserve supported matches and reject evidenced conflicts; do not optimize by refusing all cases. Return full source or ABSTAIN.'


def prepare(root,fixture_roles=None):
    if root.exists():raise FileExistsError('new A3b run required')
    original=read(OLD/'protocol.json');roles=B.learning.load_dataset(Path(original['dataset'])) if fixture_roles is None else B.learning.validate_rows(fixture_roles)
    root.mkdir(parents=True)
    plan=deepcopy(original);initial,revision=prompts()
    plan.update(version=VERSION,run_id='a3b:'+root.parent.name+':'+root.name,scope='PAIRED_DEVELOPMENT_NOT_GENERALIZATION',engineering_fixture=fixture_roles is not None,
        max_calls=12,max_tokens=4*(262400+4096)+8*(393472+4096),max_cost_microusd=5500000,
        worker_calls=12*(sum(map(len,roles.values()))+18*sum(r['label']=='MATCH' for rs in roles.values() for r in rs))+4*len(roles['TRAIN']),
        environment_steps=2*12*sum(r['label']=='MATCH' for rs in roles.values() for r in rs)*50,
        roles_sha256=fingerprint(roles),prompt_sha256={'initial':fingerprint(initial),'revision':fingerprint(revision)},
        branches=['R0','R1'],branch_limit=1,validation_role='PREVIOUSLY_INSPECTED_DEVELOPMENT',
        exposed_regression_allowed=False,A4_allowed=False,paid_api_authorized=False,
        pairing='same parent and exact selected TRAIN IDs; compute both payloads before sending either; overlength blocks both',
        selection='unchanged A3 eligibility/order; stable candidate IDs include branch suffix for deterministic final tie',
        historical_sha256=archived_hashes())
    for f in [Path(__file__),PROMPT_FILE,PROMPT_FILE.with_name('A3b_Semantic_Contract.md'),B.ROOT/'scripts/audit_alfworld_a3b.py',B.ROOT/'FlowEvo/src/alfworld_/applicability_semantic_feedback.py',B.ROOT/'FlowEvo/src/alfworld_/applicability_paired_metrics.py']:
        plan['code_sha256'][str(f.resolve())]=sha(f)
    packet=B.learning.training_packet(roles['TRAIN'],B.CODE.read_text());plan['packet_sha256']=fingerprint(packet)
    plan['pricing_reference']=dict(plan['pricing_reference'],verified_date='2026-11-14',cache_hit_peak_per_million=.006,off_peak_multiplier=.5)
    plan['A3_ready']=False
    plan['qualification_note']='Original qualification preserved; exposed regression prohibited, selected candidate stays pending with no execution permission.'
    plan['selection_dataset_role']='Previously inspected validation / development evidence'
    plan['A4_rules_sha256']=sha(B.ROOT/'runs/alfworld_route_a_a3_launch_check_20261114_01/A4_PreOutcome_Rules.json')
    initial_wire=B.wire(root,{'candidate_id':'candidate_0','training_input':packet},initial,.6,plan['input_policy'])
    plan['initial_wire_sha256']=fingerprint(initial_wire);plan['initial_input_upper']=len(canonical(initial_wire).encode())+256
    B.pilot.commit(root/'protocol.json',plan);B.pilot.commit(root/'roles.private.json',roles);B.pilot.commit(root/'learning.private.json',packet)
    B.pilot.commit(root/'authorization.template.json',dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=plan['model'],
        protocol=VERSION+':'+fingerprint(plan),max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=False))
    return plan


def preflight(root,authorization=None,paid=False):
    plan=read(root/'protocol.json');roles=read(root/'roles.private.json');B.learning.validate_rows(roles)
    if plan['version']!=VERSION or fingerprint(roles)!=plan['roles_sha256'] or sha(B.CODE)!=plan['recovery_sha256']:raise PermissionError('data/version drift')
    if any(sha(p)!=h for p,h in {**plan['code_sha256'],**plan['historical_sha256']}.items()):raise PermissionError('source/history drift')
    if fingerprint(read(root/'learning.private.json'))!=plan['packet_sha256']:raise PermissionError('packet drift')
    if sha(B.ROOT/'runs/alfworld_route_a_a3_launch_check_20261114_01/A4_PreOutcome_Rules.json')!=plan['A4_rules_sha256']:raise PermissionError('A4 boundary drift')
    if plan['rules']!=B.learning.SELECTION_RULES or sha(Path(plan['dataset'])/'dataset.json')!=plan['dataset_sha256']:raise PermissionError('rules/data drift')
    if paid:
        if plan['engineering_fixture'] or roles!=B.learning.load_dataset(Path(plan['dataset'])):raise PermissionError('fixture or data drift')
        if not B.learning.coverage(roles)['ready'] or not read(Path(plan['dataset'])/'dataset.json').get('A3_data_ready'):raise PermissionError('DATA_COVERAGE_BLOCKED')
        required=dict(read(root/'authorization.template.json'),paid_api_authorized=True)
        if required!={'run_id':plan['run_id'],'protocol_hash':fingerprint(plan),'model':plan['model'],'protocol':VERSION+':'+fingerprint(plan),
                      'max_cost_microusd':plan['max_cost_microusd'],'paid_api_authorized':True} or authorization!=required:
            raise PermissionError('NEW_A3B_AUTHORIZATION_REQUIRED')
    return plan,roles


def train_diagnostics(root,parent,roles,runner,registry):
    if parent['status']!='STATIC_PASSED':return {}
    template=B.FailureOperator.from_dict(parent['registration']['card']);rows={fingerprint(r['sample_id']):r for r in roles['TRAIN']};result={}
    try:
        source,branches=instrument(parent['code'])
        card=card_for(root,source,template,registry,parent['candidate_id']+'_train_trace')
        diagnostic_error=None
    except (ValueError,SyntaxError,RecursionError) as e:
        card=None;diagnostic_error=type(e).__name__+': '+str(e)[:1000]
    for old in parent['train']:
        if card is None or old['actual']=='ERROR':
            tr=dict(status='UNDETERMINED',reason=diagnostic_error or 'original runtime/envelope error; no causal trace claimed')
        else:
            ctx=dict(rows[old['sample_id']]['candidate_context'],state={});d=B.learned_decision(runner,card,ctx);tr=decode_trace(d,branches,old)
            if not tr['decision_preserved']:tr=dict(status='UNDETERMINED',reason='diagnostic copy differed; discarded branch claim',execution_id=d['execution_id'])
        result[old['sample_id']]=dict(candidate_version=parent['version'],sample_id=old['sample_id'],split='TRAIN',trace=tr,category=category(old,tr))
    return result


def run(root,sender=None,authorization=None,after_attempt=None):
    plan,roles=preflight(root,authorization,paid=sender is None);engineering=sender is not None
    backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    if backend.manifest()!=plan['worker'] or B.pilot.environment_manifest(read(Path(plan['dataset'])/'protocol.json')['data_root'])!=plan['environment']:
        raise PermissionError('Worker/environment drift')
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget=B.create_accounts(root,plan);provider=SimpleNamespace(events=B.EvidenceStore(root/'provider.jsonl'))
        runner=B.EnvironmentPolicyRunner(backend,root/'worker.jsonl',budget)
        registry=B.FailureOperatorRegistry(root/'registry.jsonl',B.FailureEvidenceStore(root/'failures.jsonl'))
        receipts=B.pilot.EnvironmentReceipts(root/'environment.jsonl',plan['environment_steps'])
        B.pilot.check_run(budget,provider,runner,None)
        if (root/'result.json').exists():
            result=read(root/'result.json')
            if result['protocol_sha256']!=fingerprint(plan):raise PermissionError('result protocol drift')
            return result
        known=B.register_source(root,registry,runner,roles,plan);initial,revision=prompts();packet=read(root/'learning.private.json');attempts=[];seen={}
        def one(cid,branch,parent,message):
            name=cid+'/'+branch;directory=root/name;rev=branch!='initial';prompt=revision if rev else initial
            pol=plan['revision_policy' if rev else 'input_policy'];wire=B.wire(root,message,prompt,.6,pol)
            B.pilot.commit(directory/'request.private.json',dict(payload=message,wire=wire,parent_version=parent['version'] if parent else None))
            response=B.stage_request(root,name,'analyze',message,B.parse_delivery,budget,sender=sender,authorization=authorization,
                protocol=VERSION+':'+fingerprint(plan),analysis_prompt=prompt,temperature=.6,input_policy=pol)
            parsed=B.delivery(response);code=parsed.get('submitted_code') or (parsed.get('proposal') or {}).get('code')
            a=dict(candidate_id=cid if not rev else cid+'_'+branch,branch=branch,base_id=cid,revision=int(rev),
                parent_version=parent['version'] if parent else None,parent_source_sha256=parent.get('code_sha256') if parent else None,
                version=fingerprint([response['response_sha256'],code,name,plan['roles_sha256']]),status=parsed['status'],delivery=parsed,code=code,
                code_sha256=B.pilot.save_exact_source(directory/'gate.py',code) if code else None,usage=B.trusted_usage(response['raw_response']),
                request_id=response['id'],response_sha256=response['response_sha256'],origin='MOCK' if engineering else 'DEEPSEEK')
            if parsed['status']=='PROPOSE':
                if a['code_sha256'] in seen:
                    previous=seen[a['code_sha256']];a.update(static=previous['static'],status=previous['status'],duplicate_of=previous['version'])
                    if 'train' in previous:
                        a['registration']=previous['registration']
                        for key in ('train','validation'):
                            a[key]=[dict(r,candidate_id=a['candidate_id'],version=a['version']) for r in previous[key]]
                else:
                    try:a['static']=B.static_check_detailed(B.worker_artifact(code));a['status']='STATIC_PASSED' if a['static']['passed'] else 'STATIC_REJECTED'
                    except (ValueError,SyntaxError,RecursionError) as e:a.update(status='GATE_CONTRACT_REJECTED',static={'passed':False,'error':str(e)})
                    if a['status']=='STATIC_PASSED':
                        reg=B.pilot.register(directory,dict(parsed['proposal'],code=B.worker_artifact(code)),response,
                            {'version':a['version'],'parent':a['parent_version']},list(known),known,runner,registry,engineering=engineering,protocol=VERSION)
                        if reg['status']!='SHADOW':raise PermissionError('Shadow required')
                        a['registration']=reg;gate=B.FailureOperator.from_dict(reg['card']);recovery=B.source_card(root,registry,plan,known,a['version'])
                        a['train']=B.evaluate(roles['TRAIN'],a,gate,recovery,plan,directory/'train',runner,registry,receipts)
                        a['validation']=B.evaluate(roles['TRAIN_VALIDATION'],a,gate,recovery,plan,directory/'validation',runner,registry,receipts)
                    seen[a['code_sha256']]=a
            B.pilot.commit(directory/'attempt.json',a);attempts.append(a)
            if after_attempt:after_attempt(a)
            return a
        parents=[one('candidate_'+str(i),'initial',None,dict(candidate_id='candidate_'+str(i),training_input=packet)) for i in range(4)]
        skipped=[]
        for parent in parents:
            cid=parent['candidate_id']
            if parent['status']=='ABSTAIN':skipped.append({'candidate':cid,'reason':'PARENT_ABSTAIN'});continue
            traces=train_diagnostics(root/cid,parent,roles,runner,registry)
            r0,r1,binding=paired_feedback(parent,roles['TRAIN'],plan['revision_policy'],traces)
            try:
                for msg in (r0,r1):B.wire(root,msg,revision,.6,plan['revision_policy'])
            except ValueError as e:
                if str(e)!='EVIDENCE_REPRESENTATION_LIMIT':raise
                skipped.append({'candidate':cid,'reason':'PAIRED_INPUT_LIMIT'});continue
            B.pilot.commit(root/cid/'paired_feedback.private.json',dict(binding,R0=r0,R1=r1,diagnostics=traces))
            one(cid,'R0',parent,r0);one(cid,'R1',parent,r1)
        selection=B.learning.select(attempts,roles,engineering=engineering)
        B.pilot.commit(root/'selection.json',selection)
        chosen=next((a for a in attempts if selection.get('selected') and a['version']==selection['selected']['version']),None)
        frozen=dict(status=selection['status'],selected=selection.get('selected'),permission='SHADOW',origin='MOCK_ENGINEERING' if engineering else 'REAL_MODEL',
                    publication_authorized=False,A4_authorized=False,protocol_sha256=fingerprint(plan))
        if chosen:
            (root/'frozen_candidate').mkdir(exist_ok=True)
            frozen['source_sha256']=B.pilot.save_exact_source(root/'frozen_candidate/gate.py',chosen['code'])
        B.pilot.commit(root/'Final_Candidate_Freeze.json',frozen)
        # Exposure regression is prohibited in A3b; selected remains pending, never published.
        result=dict(status='A3B_ENGINEERING_COMPLETED' if engineering else 'A3B_COMPLETED',attempts=attempts,skipped=skipped,
            selection=selection,paid_requests=0 if engineering else budget.calls,budget=budget.snapshot(),environment=dict(receipts.started),
            protocol_sha256=fingerprint(plan),confirmatory_generalization='NOT_ESTABLISHED',exposed_regression='PROHIBITED_NOT_RUN',A4='NOT_RUN')
        B.pilot.check_run(budget,provider,runner,None)
        B.pilot.commit(root/'A3b_Results.json',analyze(result))
        return B.pilot.commit(root/'result.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','preflight','run']);p.add_argument('--output',type=Path,required=True);p.add_argument('--authorization',type=Path)
    a=p.parse_args();root=a.output.resolve()
    if a.command=='prepare':result=prepare(root)
    elif a.command=='preflight':plan,roles=preflight(root);result={'status':'PENDING_NEW_AUTHORIZATION','protocol_sha256':fingerprint(plan)}
    else:
        if a.authorization is None:p.error('explicit A3b authorization file required')
        result=run(root,authorization=read(a.authorization))
    print(canonical({k:v for k,v in result.items() if k in ['status','run_id','selection','protocol_sha256']}))
