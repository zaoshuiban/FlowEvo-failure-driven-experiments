"""Engineering fixtures only; not learned declarations or model semantics."""
import sys,copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.math_goal_consistency import *
def main():
 vocab={'objects':dict(inputs=[],output='set',definition='engineering object set'),
        'count':dict(inputs=['set'],output='integer',definition='engineering cardinality'),
        'total':dict(inputs=['set'],output='integer',definition='engineering sum'),
        'allowed':dict(inputs=[],output='proposition',definition='engineering premise allowed'),
        'forbidden':dict(inputs=[],output='proposition',definition='engineering premise forbidden')}
 def term(s,*args):return dict(symbol=s,arguments=list(args))
 goal=term('count',term('objects'))
 cap=dict(code_sha256='frozen-fixture',vocabulary_sha256=fingerprint(vocab),goal=goal,requires={'reuse':term('forbidden')},parameter_schema=dict(type='object',properties={'n':{'type':'integer'}},required=['n'],additionalProperties=False),limitations=['engineering mock'])
 p=dict(problem_sha256='question-fixture',vocabulary_sha256=fingerprint(vocab),goal=goal,conditions=cap['requires'],parameters={'n':2},uncertain=False)
 def run(c=cap,q=p,v=vocab):return compare_goal(c,q,v,code_sha256='frozen-fixture',problem_sha256='question-fixture')
 checks={}
 def expect(name,q,status,c=cap,v=vocab):checks[name]=run(c,q,v)['status']==status
 expect('same_tree',p,'MATCH')
 expect('same_result_type_different_objective',dict(p,goal=term('total',term('objects'))),'DECLINE')
 expect('opposite_premise',dict(p,conditions={'reuse':term('allowed')}),'DECLINE')
 expect('missing_premise',dict(p,conditions={}),'UNKNOWN')
 expect('additional_premise',dict(p,conditions=dict(p['conditions'],extra=term('allowed'))),'UNKNOWN')
 expect('unstated_is_unknown',dict(p,conditions={'reuse':None}),'UNKNOWN')
 expect('unknown_goal',dict(p,goal=None),'UNKNOWN')
 expect('nested_unknown',dict(p,goal=term('count',None)),'UNKNOWN')
 expect('type_error',dict(p,goal=term('count',term('allowed'))),'UNKNOWN')
 expect('arity_error',dict(p,goal=term('count')),'UNKNOWN')
 expect('keyword_instead_of_term',dict(p,goal='count objects'),'UNKNOWN')
 expect('unknown_symbol',dict(p,goal=term('not_in_registry')),'UNKNOWN')
 expect('free_text_hidden_field',dict(p,goal=dict(goal,contains='prime')),'UNKNOWN')
 expect('uncertain',dict(p,uncertain=True),'UNKNOWN')
 expect('unknown_type',dict(p,uncertain='false'),'UNKNOWN')
 expect('bool_not_integer',dict(p,parameters={'n':True}),'UNKNOWN')
 expect('extra_parameter',dict(p,parameters={'n':2,'x':3}),'UNKNOWN')
 expect('wrong_problem_binding',dict(p,problem_sha256='different'),'UNKNOWN')
 expect('changed_code',p,'UNKNOWN',c=dict(cap,code_sha256='changed'))
 expect('changed_vocabulary',p,'UNKNOWN',v=dict(vocab,alias=vocab['count']))
 expect('schema_network_reference',p,'UNKNOWN',c=dict(cap,parameter_schema=dict(type='object',additionalProperties=False,properties={'n':{'$ref':'https://example.invalid/schema'}})))
 checks['no_permission_from_match']=run()['execute_authorized'] is False
 checks['no_truth_claim']=run()['semantic_truth_verified'] is False
 checks['parser_blind_to_candidate']=set(problem_view('fixture',vocab))=={'protocol','problem','vocabulary','instruction'}
 checks['declaration_blind_to_test']=set(declaration_view('fixture source'))=={'protocol','source','instruction'}
 out=ROOT/'reports/math_goal_consistency_20261102';out.mkdir(parents=True,exist_ok=True)
 (out/'zero_api_checks.json').write_text(json.dumps(dict(origin='HUMAN_ENGINEERING_FIXTURES',paid_calls=0,checks=checks,passed=sum(checks.values()),total=len(checks)),indent=2))
 print(json.dumps(checks,indent=2));assert all(checks.values())
if __name__=='__main__':main()
