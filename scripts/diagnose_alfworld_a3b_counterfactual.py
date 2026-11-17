"""TRAIN-only single-factor diagnostic copies. Never imported by learner/runtime."""
import ast
from copy import deepcopy
from pathlib import Path
import argparse
import run_alfworld_applicability_multicandidate as B
from audit_alfworld_a3b import OLD,setup,card_for,archived_hashes
from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read

HELPER='''\ndef _diagnostic_binding(goal, actual):
    g=goal.lower().strip().rstrip('.!?').split()
    a=actual.lower().strip().split()
    if g and g[0] in ('a','an','the','some'): g=g[1:]
    return g==a or (a and a[-1].isdigit() and g==a[:-1])
'''

def copy_source(source,kind):
    tree=ast.parse(source);changed=0
    class Change(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal changed
            if kind in ('binding','binding_raw') and ast.unparse(n) in ('_norm(final_target).lower() != _norm(rec).lower()', '_norm(target).lower() != _norm(rec).lower()'):
                changed+=1;name='final_target' if 'final_target' in ast.unparse(n) else 'target'
                return ast.parse('not _diagnostic_binding('+name+', rec)',mode='eval').body
            return self.generic_visit(n)
        def visit_If(self,n):
            nonlocal changed
            n=self.generic_visit(n)
            if kind=='instance' and ast.unparse(n.test)=='rec_nums':
                changed+=1;n.test=ast.parse('rec_nums and dest_nums',mode='eval').body
            return n
        def visit_FunctionDef(self,n):
            nonlocal changed
            if kind=='grammar' and n.name=='_goal_object':
                # Only extend the prefix grammar, keep original return/normalization/binding.
                n=self.generic_visit(n)
                marker=ast.parse("if g.startswith(('heat ', 'cool ', 'clean ')) and ' and put it ' in g:\n    head, tail = g.split(' and put it ', 1)\n    g = 'put ' + head.split(' ',1)[1] + ' ' + tail").body
                n.body[1:1]=marker;changed+=1;return n
            return self.generic_visit(n)
    tree=Change().visit(tree);ast.fix_missing_locations(tree)
    if changed!=1:raise ValueError(('expected one semantic edit',kind,changed))
    helper=HELPER if kind=='binding' else HELPER.replace(".rstrip('.!?')",'').replace("    if g and g[0] in ('a','an','the','some'): g=g[1:]\n",'')
    return ast.unparse(tree)+(helper if kind in ('binding','binding_raw') else '')


def run(root,binding_only=False):
    before=archived_hashes();roles=read(OLD/'roles.private.json');data={fingerprint(r['sample_id']):r for r in roles['TRAIN']}
    # Frozen before execution: every TRAIN row, initial versions only, no outcome-based choice.
    specs=[(0,'punctuation'),(0,'binding'),(1,'punctuation'),(1,'grammar'),(1,'grammar_plus_punctuation'),(2,'punctuation'),(2,'binding'),(3,'instance')]
    if binding_only:specs=[(0,'binding_raw'),(2,'binding_raw')]
    plan,runner,registry=setup(root,600);B.pilot.commit(root/'diagnostic_plan.json',{'scope':'DIAGNOSTIC_ONLY','specs':specs,'ids':list(data),'no_environment':True,'no_learning':True})
    original=read(OLD/'result.json');rows=[]
    for number,kind in specs:
        a=next(a for a in original['attempts'] if a['candidate_id']=='candidate_'+str(number) and a['revision']==0)
        source=a['code'] if kind=='punctuation' else copy_source(a['code'],'grammar' if kind=='grammar_plus_punctuation' else kind)
        template=B.FailureOperator.from_dict(a['registration']['card']);card=card_for(root,source,template,registry,a['candidate_id']+'_'+kind)
        B.pilot.save_exact_source(root/(a['candidate_id']+'_'+kind+'.raw.py'),source)
        for old in a['train']:
            ctx=deepcopy(data[old['sample_id']]['candidate_context']);ctx['state']={}
            if kind in ('punctuation','grammar_plus_punctuation'):ctx['goal']=ctx['goal'].rstrip().rstrip('.!?')
            d=B.learned_decision(runner,card,ctx)
            rows.append(dict(scope='DIAGNOSTIC_ONLY',candidate=a['candidate_id'],original_version=a['version'],intervention=kind,
                sample_id=old['sample_id'],game_sha256=data[old['sample_id']]['game_sha256'],expected=old['expected'],before=old['actual'],
                after=d['status'],reason=d['reason'],execution_id=d['execution_id'],source_sha256=fingerprint(source)))
        print(number,kind,'done',flush=True)
    assert before==archived_hashes()
    return B.pilot.commit(root/'A3b_Counterfactual_Diagnostics.json',dict(scope='DIAGNOSTIC_ONLY',rows=rows,paid_requests=0,
        environment_steps=0,worker_calls=runner.budget.tool_calls,historical_unchanged=True,not_model_learned=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binding-only',action='store_true');a=p.parse_args();run(a.output.resolve(),a.binding_only)
