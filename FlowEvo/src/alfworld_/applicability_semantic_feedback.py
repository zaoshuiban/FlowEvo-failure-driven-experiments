"""A3b diagnostics and paired feedback; never supplies a runtime goal parser."""
import ast
from copy import deepcopy
from failure_evo.contracts import fingerprint,canonical
from . import recovery_applicability_learning as L
from . import recovery_learning_input as I

VERSION='route-a3b-semantic-feedback-v1'
MARKER='|A3B_RETURN:'


def instrument(source):
    tree=ast.parse(source);branches={}
    if any(isinstance(n,ast.Name) and n.id=="_a3b_return_receipt" or isinstance(n,ast.FunctionDef) and n.name=="_a3b_return_receipt" for n in ast.walk(tree)):
        raise ValueError("TRACE_NAME_COLLISION")
    class Tag(ast.NodeTransformer):
        def visit_FunctionDef(self,node):
            if node.name!='applicability_gate':return node
            def walk(n,conditions):
                if isinstance(n,(ast.FunctionDef,ast.Lambda)) and n is not node:return
                if isinstance(n,ast.Return):
                    branches[str(n.lineno)]=dict(line=n.lineno,function=node.name,
                        enclosing_conditions=conditions,return_expression=ast.get_source_segment(source,n.value))
                for child in ast.iter_child_nodes(n):
                    walk(child,conditions+[dict(line=n.lineno,expression=ast.get_source_segment(source,n.test),
                         arm='body' if child in n.body else 'else')] if isinstance(n,ast.If) and child in n.body+n.orelse else conditions)
            walk(node,[])
            class Returns(ast.NodeTransformer):
                def visit_FunctionDef(self,n):
                    return self.generic_visit(n) if n is node else n
                def visit_Return(self,n):
                    return ast.copy_location(ast.Return(ast.Call(ast.Name('_a3b_return_receipt',ast.Load()),[n.value or ast.Constant(None),ast.Constant(n.lineno)],[])),n)
            return Returns().visit(node)
    tree=Tag().visit(tree);ast.fix_missing_locations(tree)
    helper='''\ndef _a3b_return_receipt(value, line):
    if not isinstance(value, dict) or set(value) != {'status', 'reason'} or not isinstance(value['reason'], str):
        return value
    return {'status':value['status'], 'reason':value['reason'][:340]+'|A3B_RETURN:'+str(line)}
'''
    return ast.unparse(tree)+helper,branches


def decode_trace(decision,branches,original):
    reason=decision['reason'];line=reason.rsplit(MARKER,1)[-1] if MARKER in reason else None
    branch=branches.get(line)
    return dict(status='RETURN_SITE_OBSERVED' if branch else 'UNDETERMINED',
        decision_preserved=decision['status']==original['actual'],reached_return=branch,
        note='Return site and enclosing syntax, not proof of deepest cause or every executed predicate.')


def category(row,trace):
    if row['actual']=='ERROR':return 'H_INTERFACE_OR_RUNTIME_ERROR'
    if row['actual']==row['expected']:return 'G_CORRECT_DECISION'
    if row['actual']=='UNKNOWN' and 'pars' in row['reason'].lower():return 'A_OBSERVED_GOAL_PARSE_FAILURE'
    # A textual candidate reason is not a causal diagnosis.
    return 'I_UNEXPLAINED_CAUSE'


def paired_feedback(parent,train,policy,train_traces):
    r0=I.revision(parent,train,policy)
    allowed={fingerprint(r['sample_id']) for r in train}
    ids=[x['sample_id'] for x in r0['own_train_feedback']]
    r1=deepcopy(r0);diagnostics=[]
    for item in r1['own_train_feedback']:
        sid=item['sample_id'];tr=train_traces.get(sid)
        if sid not in allowed:raise PermissionError('non-TRAIN feedback')
        if tr is not None and (tr['candidate_version']!=parent['version'] or tr['split']!='TRAIN' or tr['sample_id']!=sid):
            raise PermissionError('foreign diagnostic evidence')
        diagnostics.append(dict(sample_id=sid,expected=item['supervision']['label'],actual=item['candidate_self_report']['status'],
            observed_reason=item['candidate_self_report']['reason'],candidate_reason_is_fact=False,
            reached_code_branch=tr['trace'] if tr else {'status':'UNDETERMINED'},
            failure_category=tr['category'] if tr else 'I_UNEXPLAINED_CAUSE',
            context_evidence_ref={'sample_id':sid,'path':'own_train_feedback[].public_evidence','sha256':fingerprint(item['public_evidence'])},
            revision_goal='Correct the demonstrated TRAIN disagreement while retaining supported matches and conflict/uncertainty protection. No repair algorithm is supplied.'))
    r1['structured_counterexamples']=diagnostics
    r1['feedback_interpretation']='Structured execution diagnosis adds evidence; not a formatting-only comparison.'
    if [x['sample_id'] for x in r1['own_train_feedback']]!=ids:raise PermissionError('paired evidence mismatch')
    return r0,r1,dict(sample_ids=ids,sample_ids_sha256=fingerprint(ids),parent_version=parent['version'],
        feedback_r0_sha256=fingerprint(r0),feedback_r1_sha256=fingerprint(r1))
