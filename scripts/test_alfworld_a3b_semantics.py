"""24 prespecified synthetic diagnostics. Neither training data nor learned results."""
import argparse
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from alfworld_.recovery_applicability import placement_goal
from audit_alfworld_a3b import OLD,setup,card_for
from failure_evo.math_stream import read
import run_alfworld_applicability_multicandidate as B


def cases():
    parse=[('Put a pear in drawer.',('pear','drawer',None,None)),('Put a pear in drawer 2.',('pear','drawer','2',None)),
        ('Heat a pear and put it in cabinet.',('pear','cabinet',None,'heat')),('Cool a pear and put it in cabinet.',('pear','cabinet',None,'cool')),
        ('Clean a mug and put it in drawer.',('mug','drawer',None,'clean')),('Put a clean mug in drawer.',('mug','drawer',None,'clean')),
        ('Put a pear in drawerbox.',('pear','drawerbox',None,None)),('Make everything beautiful.',None)]
    base=dict(goal='put a pear in drawer',observation='The drawer 1 is closed.',admissible_commands=['open drawer 1','look'],
        history=[dict(action='inventory',observation='You are carrying: pear 1.'),dict(action='move pear 1 to drawer 1',observation='Nothing happens.')])
    gates=[]
    def add(name,expected,why,**changes):gates.append(dict(id=name,layer='GATING',context=dict(deepcopy(base),**changes),expected=expected,semantic_review=why))
    add('category_instance','MATCH','Held task object, failed final delivery into same-category closed destination, and live open action.')
    add('punctuation','MATCH','A final period changes no task meaning.',goal='put a pear in drawer.')
    add('explicit_conflict','DECLINE','Requested instance 2 differs from failed instance 1.',goal='put a pear in drawer 2')
    add('category_prefix_conflict','DECLINE','drawerbox and drawer are distinct object categories.',goal='put a pear in drawerbox')
    add('processing_not_known','UNKNOWN','Visible suffix does not establish required heating; cannot infer not heated.',goal='heat a pear and put it in drawer')
    add('processing_completed','MATCH','Public successful same-instance heating precedes final delivery.',goal='heat a pear and put it in drawer',history=[dict(action='heat pear 1 with microwave 1',observation='You heat the pear 1 using the microwave 1.'),*base['history']])
    add('intermediate_not_final','DECLINE','Frozen skill repairs failed final delivery; microwave is intermediate and drawer final.',goal='heat a pear and put it in drawer',history=[base['history'][0],dict(action='move pear 1 to microwave 1',observation='Nothing happens.')],admissible_commands=['open microwave 1'])
    add('stale_success','DECLINE','Latest move already succeeded; historical no-effect does not justify recovery.',history=[*base['history'],dict(action='move pear 1 to drawer 1',observation='You move the pear 1 to the drawer 1.')])
    runtime=[]
    for name,change in [('empty_goal',{'goal':''}),('empty_history',{'history':[]}),('two_visible_instances',{'admissible_commands':['open drawer 1','open drawer 2']}),
        ('missing_observation',{'observation':''}),('state_outer_only',{'state':{'must_not_leak':True}}),('scope_outer_only',{'public_history_scope':'must_not_leak'}),
        ('normal',{}),('empty_actions',{'admissible_commands':[]})]:
        runtime.append(dict(id=name,layer='INTERFACE',context=dict(deepcopy(base),**change),expected='UNKNOWN',semantic_review='Engineering probe verifies exactly four keys; UNKNOWN is fixture behavior, not a learned prediction.'))
    return dict(parse=[dict(id='parse_'+str(i),layer='PARSING',goal=g,expected=list(e) if e else None,semantic_review='Manually authored object, final destination, instance and operation; no dataset/test examples copied.') for i,(g,e) in enumerate(parse)],gating=gates,interface=runtime)


def run(root):
    root.mkdir(parents=True,exist_ok=True);spec=cases();B.pilot.commit(root/'A3b_Semantic_Unit_Tests.json',dict(scope='SYNTHETIC_ENGINEERING_ONLY',cases=spec,review='Explicit per-case mathematical/task semantics above; not an independent researcher endorsement.'))
    _,runner,registry=setup(root,32);a=read(OLD/'result.json')['attempts'][1];template=B.FailureOperator.from_dict(a['registration']['card'])
    gate=card_for(root,a['code'],template,registry,'archived_candidate_1');probe='''def applicability_gate(context):
    if set(context) != {'goal','observation','admissible_commands','history'}:
        return {'status':'DECLINE','reason':'unexpected keys'}
    return {'status':'UNKNOWN','reason':'ENGINEERING_INTERFACE_ONLY'}
'''
    interface=card_for(root,probe,template,registry,'engineering_probe');results=[]
    for x in spec['parse']:
        p=placement_goal(x['goal']);actual=[p[0].category,p[1].category,p[1].number,p[2]] if p else None
        results.append(dict(x,actual=actual,passed=actual==x['expected'],origin='EXISTING_HOST_PARSER_DIAGNOSTIC_NOT_INJECTED'))
    for layer,card in [('gating',gate),('interface',interface)]:
        for x in spec[layer]:
            d=B.learned_decision(runner,card,dict(x['context'],state=x['context'].get('state',{})))
            results.append(dict(x,actual=d['status'],reason=d['reason'],execution_id=d['execution_id'],passed=d['status']==x['expected']))
    return B.pilot.commit(root/'semantic_results.json',dict(results=results,worker_calls=runner.budget.tool_calls,paid_requests=0,
        note='Archived model gate may fail semantic requirements; test harness observes failures, not claims newly learned semantic competence.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output.resolve())
