"""Persist explicitly reviewed archive identities. Similarity scores never grant identity."""
import json, re, hashlib, collections, csv
from pathlib import Path
from audit_math_stream200_sources import ROOT, OUT, DATA, save, sha

# Explicit item reviews, including mathematical constraints, performed 2026-11-02.
# This list is NOT dynamically populated by a similarity threshold.
APPROVED = {2577,3556,4044,3241,2384,1363,1382,3872,3909,3830,1649,3917,1198,1795,4052,3188,3855,4021,3278,1410,1362,1162,3853,558,1333,791,1539,3207,3250,1488,3897,3939,2420,3792,3879,3871,1464,1104,2293,1287,2655,3711,3227,3793,3828,3234,1384,1073,3204,1535,3213,1147,4157,3240,1067,2186,1257,1484,1729,1368,3937,775,4152,3955,3148,1329,3839,3829,1174,1949,831,353,2500,1628,2504,1243,1571,1177}
REJECTED = {1638:'Different number theoretic statement and constraints.',3647:'Different quantifier and arithmetic condition.',3583:'Wrong candidate; separately recovered as APMO 1998 P5.'}

def original(c):
    k=c['archive'].split('-')
    if k[0]=='hmmt':return '/'.join(['HMMT',k[1],k[2],k[3],'P'+c['item']])
    return '/'.join([{'apmo':'APMO','imosl':'IMO-SL','imo':'IMO','putnam':'PUTNAM','putnamk':'PUTNAM'}[k[0]],k[1],c['item'] if k[0] in ('imosl','putnam','putnamk') else 'P'+c['item']])

def main():
    protocol=json.loads((DATA/'protocol.json').read_text())
    assert all(sha((DATA/k).read_bytes())==v for k,v in protocol['files'].items())
    candidates=json.loads((OUT/'private/item_review_candidates.json').read_text())
    metas={x['task_id']:x for x in map(json.loads,(DATA/'host/task_metadata.jsonl').read_text().splitlines())}
    reviewed={};risks=[]
    for x in candidates:
        tid=x['task_id'];n=int(tid.split('-')[-1]);m=metas[tid]
        r=dict(task_id=tid,sequence=m['sequence'],source_original_id='UNKNOWN',lineage_id='UNKNOWN',parameter_variant_id='UNKNOWN',
            mechanism_family='UNKNOWN',dataset_role='PREQUENTIAL_STREAM',provenance_status='UNKNOWN',
            problem_sha256=sha(x['problem'].encode()),dataset_record=dict(revision=m['revision'],row=m['row'],source_family=m['source']),
            template_proxy_sha256=m['template_proxy_sha256'],identity_review='No certified year/item; a distinct row or text hash is not an original.',source_evidence=[])
        if n in APPROVED:
            c=x['candidates'][0];oid=original(c)
            r.update(source_original_id=oid,lineage_id=oid,provenance_status='ARCHIVE_ITEM_VERIFIED',relation='SAME_ORIGINAL_STATEMENT',
                parameter_variant_id='ORIGINAL_PARAMETERS',identity_review='Codex host-side item comparison: objective, constraints and numerical parameters agree; not a generated learner claim.',
                source_evidence=[{k:c[k] for k in ('url','pdf_sha256','page','item','authority','archive')}])
        if n in (1613,3583,2329,3796):
            key='apmo-1998' if n in (1613,3583) else 'imc-2020-6';rec=json.loads((OUT/f'private/sources/{key}.receipt.json').read_text())
            oid='APMO/1998/P5' if n in (1613,3583) else 'IMC/2020/P6'
            r.update(source_original_id=oid,lineage_id=oid,provenance_status='ARCHIVE_ITEM_VERIFIED',parameter_variant_id='ORIGINAL_PARAMETERS',relation='SAME_ORIGINAL_REPHRASE',
                identity_review='Host reviewed equal mathematical objective and parameters; IMC residue representatives 1..p and Z_p are equivalent. APMO cube root visually checked.',
                source_evidence=[dict(url=rec['url'],pdf_sha256=rec['sha256'],page=1,item='5' if key.startswith('apmo') else '6',authority=rec['authority'],archive=key)])
        flags=[]
        if re.search(r'\bestimat|your score|points\.',x['problem'],re.I):flags.append('ESTIMATION_OR_PARTIAL_CREDIT_REQUIRES_SCORING_SEMANTICS_REVIEW')
        if re.search(r'(find|determine) all|two possible values',x['problem'],re.I):flags.append('SET_VALUED_OBJECTIVE_REQUIRES_COMPLETENESS_REVIEW')
        if n==2293:flags.append('ORIGINAL_PARTIAL_CREDIT_RULE_OMITTED_FROM_DATASET')
        r['scoring_review_flags']=flags
        if flags:risks.append(dict(task_id=tid,flags=flags,source_original_id=r['source_original_id'],disposition='DO_NOT_CREATE_CONFIRMED_WRONG_UNTIL_HOST_SCORING_REVIEW'))
        reviewed[tid]=r
    groups=collections.defaultdict(list)
    for r in reviewed.values():
        if r['lineage_id']!='UNKNOWN':groups[r['lineage_id']].append(r['task_id'])
    save(OUT/'provenance.json',reviewed)
    save(OUT/'lineage_groups.json',dict(verified_original_groups=dict(groups),unknown_task_ids=[t for t,r in reviewed.items() if r['lineage_id']=='UNKNOWN'],
        policy='UNKNOWN is not one common lineage and is not a unique original. Block cross-original claims. Known aliases/parameter variants share lineage.',
        not_merged=[dict(tasks=['omni-hard200-row-1539','omni-hard200-row-3278'],reason='Different base, expression and requested quantity; generic digit vocabulary is insufficient.')]))
    save(OUT/'scoring_semantics_flags.json',risks)
    save(OUT/'rejected_source_candidates.json',REJECTED)
    with (OUT/'task_provenance.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['sequence','task_id','source_original_id','lineage_id','parameter_variant_id','provenance_status']);w.writeheader()
        for r in reviewed.values():w.writerow({k:r[k] for k in w.fieldnames})
    summary=dict(total=200,verified_records=sum(r['provenance_status']=='ARCHIVE_ITEM_VERIFIED' for r in reviewed.values()),verified_originals=len(groups),
        unknown_records=sum(r['provenance_status']=='UNKNOWN' for r in reviewed.values()),duplicate_groups={k:v for k,v in groups.items() if len(v)>1},
        confirmed_parameter_variant_groups=0,scoring_flagged=len(risks),existing_dataset_hashes_unchanged=True,paid_model_calls=0,
        limitation='Unknown records and unreviewed cross-contest adaptations prevent claiming 200 independent originals. No evidence that all200 are generated from a few templates.')
    save(OUT/'source_audit_summary.json',summary);print(summary)
if __name__=='__main__':main()
