"""S22 pure paired-request preparation and scoring. No provider/send entry point."""
import copy,json,sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
from failure_evo.learning_evidence_bundle import check_packet,checkpoint_budget
from failure_evo.repair_choice_v2 import eligible_actions
from failure_evo.workflow_protocol_v2 import prepare,Limits
from failure_evo.native_adapter import SYSTEM_PROMPT
from failure_evo.selective_experience import snapshot
VERSION='s22-identical-context-one-call-v1'
INSTRUCTIONS={
 'A':'Repair the current program. Preserve its algorithm and structure where feasible, and correct the observed public failure.',
 'B':'Develop a fresh solution. You may inspect the current program, but need not preserve its algorithm or structure.'}

def freeze(packet,history,observed_at):
    state=snapshot(packet,observed_at=observed_at,history=history)
    if set(state['legal_actions'])!={'REPAIR_EXISTING','REGENERATE_FRESH'}:raise ValueError('BOTH_ACTIONS_NOT_LEGAL')
    # Identical complete public context; no source removal or feedback redaction in B.
    context=dict(task=copy.deepcopy(packet['task_public']),candidate_code=packet['code'],public_feedback=copy.deepcopy(packet['feedback']),prior_public_history=[dict(stage=h['packet']['stage'],candidate_code=h['packet']['code'],feedback=h['packet']['feedback']) for h in state['evidence']['history']],checkpoint_budget=copy.deepcopy(packet['checkpoint_budget']))
    delivery='Return one complete executable Python program in a python fence. Do not provide extended explanation, special-case samples, or merely suppress exceptions.'
    wires={}
    for arm in ('A','B'):
        messages=[dict(role='system',content=SYSTEM_PROMPT),dict(role='user',content=canonical(context)),dict(role='user',content=delivery+'\nAction instruction:\n'+INSTRUCTIONS[arm])]
        req=prepare(messages,limits=Limits(),temperature=0)
        if req.input_upper+req.output_upper>packet['checkpoint_budget']['max_tokens']-packet['checkpoint_budget']['used_tokens']:raise ValueError('INSUFFICIENT_REMAINING_TOKEN_BUDGET')
        wires[arm]=dict(wire=req.body,wire_sha256=req.sha256,input_upper=req.input_upper,output_upper=req.output_upper)
    a,b=(wires[x]['wire'] for x in ('A','B'))
    assert {k:v for k,v in a.items() if k!='messages'}=={k:v for k,v in b.items() if k!='messages'}
    assert a['messages'][:2]==b['messages'][:2]
    out=dict(version=VERSION,checkpoint_hash=fingerprint(packet),state_input_hash=state['input_hash'],context_hash=fingerprint(context),source_event_id=packet['event_id'],task_id=packet['task_id'],stage=packet['stage'],observed_at=observed_at,history_refs=[h['packet']['event_id'] for h in history],source_budget=packet['checkpoint_budget'],max_calls_per_branch=1,arms=wires,model='deepseek-flash',thinking='disabled',expected_reasoning_tokens=0,status='DRY_RUN_NOT_AUTHORIZED')
    out['freeze_hash']=fingerprint(out);return out

def classify(a,b):
    if any(v is not None and type(v) is not bool for v in (a,b)):raise ValueError('tri-state booleans required')
    if a is None or b is None:return 'UNKNOWN'
    return {(True,False):'A-only',(False,True):'B-only',(True,True):'Both-success',(False,False):'Both-fail'}[(a,b)]

def pair_result(a,b,*,online_locked=False):
    def outcome(x,strict):
        if x.get('request_state')!='COMPLETED' or x.get('infrastructure_error'):return None
        p=x.get('public_pass')
        if p is not None and type(p) is not bool:raise ValueError('invalid public outcome')
        if not strict:return p
        if not online_locked:raise ValueError('ONLINE_LOCK_REQUIRED')
        q=x.get('sealed_pass')
        if q is not None and type(q) is not bool:raise ValueError('invalid sealed outcome')
        if p is False:return False
        if p is None or q is None:return None
        return p and q
    return dict(public=classify(outcome(a,False),outcome(b,False)),strict=classify(outcome(a,True),outcome(b,True)) if online_locked else 'NOT_EVALUATED',new_calls=0)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Dry-run only: s22_ab.py PUBLIC_CHECKPOINT_JSON')
    packet=json.loads(pathlib.Path(sys.argv[1]).read_text())
    print(json.dumps(freeze(packet,[],0),ensure_ascii=False,indent=2))
