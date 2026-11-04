"""Versioned lossless reception; no mathematical repair or answer authority."""
import copy,json,hashlib
from .contracts import fingerprint
VERSION='operator-delivery-reception-v2'

def receive(stage,value):
    raw=copy.deepcopy(value);v=copy.deepcopy(value);changes=[];quarantine={};errors=[]
    if not isinstance(v,dict):return dict(version=VERSION,status='REJECTED',errors=['OBJECT_REQUIRED'],raw_sha256=fingerprint(raw))
    if 'type' in v:
        if v['type']=='json_object':quarantine['type']=v.pop('type');changes.append('FIXED_TRANSPORT_METADATA')
        else:errors.append('UNKNOWN_TYPE_METADATA')
    if stage in ('properties','review') and 'diagnostics' in v:
        if 'diagnosis' in v and v['diagnosis']!=v['diagnostics']:errors.append('CONFLICTING_DIAGNOSIS_ALIAS')
        else:v['diagnosis']=v.pop('diagnostics');changes.append('EXACT_DIAGNOSTICS_ALIAS')
    for k in ('tests','self_tests'):
        if k in v:
            if not isinstance(v[k],(list,str)):errors.append('SUPPLEMENT_TYPE:'+k)
            else:quarantine[k]=v.pop(k);changes.append('SUPPLEMENT_QUARANTINED_UNTRUSTED:'+k)
    if stage in ('code','revision','compliance'):
        required={'code'};optional={'description','applicability'}
        for k in optional:
            if k not in v:v[k]=None;changes.append('OPTIONAL_NOT_PROVIDED:'+k)
        if not isinstance(v.get('code'),str) or not v.get('code','').strip():errors.append('CODE_REQUIRED')
        for k in optional:
            if v.get(k) is not None and not isinstance(v[k],str):errors.append('DESCRIPTION_TYPE:'+k)
        protected=['code']
    elif stage=='review':required={'diagnosis','revision_plan'};optional=set();protected=['revision_plan']
    elif stage=='properties':required={'diagnosis','replacement_hypothesis','properties'};optional=set();protected=['properties','replacement_hypothesis']
    else:raise ValueError('stage')
    if set(v)-required-optional:errors.append('UNKNOWN_FIELDS:'+','.join(sorted(set(v)-required-optional)))
    if required-set(v):errors.append('MISSING_FIELDS:'+','.join(sorted(required-set(v))))
    if stage in ('review','properties'):
        for k in required-{'properties'}:
            if not isinstance(v.get(k),str) or not v.get(k,'').strip():errors.append('TEXT_REQUIRED:'+k)
    # Reception bounds are storage/safety bounds, not the execution selection budget.
    test_audit=[]
    if stage=='properties':
        props=v.get('properties')
        if not isinstance(props,list) or len(props)>32:errors.append('PROPERTIES_BOUND')
        else:
            count=0
            for i,p in enumerate(props):
                if not isinstance(p,dict) or set(p)!={'id','claim','preconditions','tests'}:errors.append('PROPERTY_FIELDS:'+str(i));continue
                if any(not isinstance(p[k],str) or not p[k].strip() for k in ['id','claim']):errors.append('PROPERTY_TEXT:'+str(i))
                pre=p['preconditions']
                if not ((isinstance(pre,str) and pre.strip()) or (isinstance(pre,list) and pre and all(isinstance(s,str) and s.strip() for s in pre))):errors.append('PRECONDITIONS:'+str(i))
                if not isinstance(p['tests'],list):errors.append('TEST_LIST:'+str(i));continue
                for j,t in enumerate(p['tests']):
                    count+=1;valid=isinstance(t,dict) and set(t)=={'relation','left','right'}
                    valid=valid and t['relation'] in ('oracle_correct','equal','different') and isinstance(t['left'],dict)
                    valid=valid and (t['right'] is None or isinstance(t['right'],dict))
                    valid=valid and (t['relation']=='oracle_correct' or isinstance(t['right'],dict))
                    test_audit.append(dict(property_index=i,test_index=j,status='EVALUABLE_SPEC' if valid else 'SEMANTICALLY_INCOMPLETE',reason=None if valid else 'NO_INFERRED_RELATION_OR_MODEL_GOLD'))
            if count>64:errors.append('TEST_BOUND')
    unchanged=all(k not in raw or fingerprint(raw[k])==fingerprint(v.get(k)) for k in protected)
    if not unchanged:raise AssertionError('reception modified protected content')
    return dict(version=VERSION,status='REJECTED' if errors else 'ACCEPTED_WITH_UNEVALUABLE_TESTS' if any(t['status']!='EVALUABLE_SPEC' for t in test_audit) else 'ACCEPTED',raw_sha256=fingerprint(raw),normalized_sha256=fingerprint(v),normalized=v,quarantine=quarantine,changes=changes,errors=errors,test_audit=test_audit,protected_content_unchanged=unchanged,code_sha256=hashlib.sha256(v['code'].encode()).hexdigest() if isinstance(v.get('code'),str) else None,model_tests_are_oracle=False)

def content_change(before,after,stage):
    if not isinstance(before,dict) or not isinstance(after,dict):
        return fingerprint(before)!=fingerprint(after)
    keys=['code'] if stage in ('code','revision','compliance') else ['diagnosis','replacement_hypothesis','properties'] if stage=='properties' else ['diagnosis','revision_plan']
    return any(fingerprint(before.get(k))!=fingerprint(after.get(k)) for k in keys)
