"""Deterministic, cluster-independent public evidence selection; no mechanism claims."""
from .contracts import canonical, fingerprint
VERSION='unlinked-evidence-retrieval-v1'

def select(memory,cutoff,*,max_records,max_bytes):
    if type(max_records) is not int or max_records<1 or type(max_bytes) is not int or max_bytes<1:
        raise ValueError('retrieval bounds')
    facts=memory.facts(cutoff);states=memory.association_states(cutoff)
    candidates=[]
    for eid,f in sorted(facts.items(),key=lambda x:(x[1]['sequence'],x[0])):
        state=states[eid];eligible=state['state'] in ('NEW','RETRY_ELIGIBLE')
        # T uses only public questions; F eligibility comes from trusted ingest.
        if memory.arm=='F' and f.get('correct') is not False:eligible=False
        candidates.append(dict(evidence_id=eid,sequence=f['sequence'],source_original_id=f['source_original_id'],
            state=state['state'],attempts=state['attempts'],eligible=eligible,
            projection_sha256=fingerprint(memory.project(f)),selected=False,reason='INELIGIBLE_STATE_OR_FEEDBACK'))
    new=[c for c in candidates if c['eligible'] and c['state']=='NEW']
    chosen=[];sources=set();used=2
    def cost(c):return len(canonical(memory.project(facts[c['evidence_id']])).encode())+1
    def add(c,reason):
        nonlocal used
        if len(chosen)>=max_records:c['reason']='RECORD_LIMIT';return False
        if used+cost(c)>max_bytes:c['reason']='INPUT_BYTE_LIMIT';return False
        chosen.append(c['evidence_id']);used+=cost(c);c.update(selected=True,reason=reason)
        if c['source_original_id']!='UNKNOWN':sources.add(c['source_original_id'])
        return True
    # Anchor on new evidence. No autonomous repeat loop on an unchanged pool.
    for c in new:
        if add(c,'NEW_EVIDENCE_ANCHOR'):break
    if chosen:
        remaining=[c for c in candidates if c['eligible'] and not c['selected']]
        while remaining:
            # Source diversity first, then old unlinked evidence and fair attempt count.
            remaining.sort(key=lambda c:(c['source_original_id']=='UNKNOWN' or c['source_original_id'] in sources,
                c['state']!='RETRY_ELIGIBLE',c['attempts'],c['sequence'],c['evidence_id']))
            c=remaining.pop(0)
            add(c,'DISTINCT_ORIGINAL_UNLINKED' if c['source_original_id']!='UNKNOWN' and c['source_original_id'] not in sources else 'UNLINKED_FALLBACK_NO_INDEPENDENCE_CLAIM')
    else:
        for c in candidates:
            if c['eligible'] and c['reason']=='INELIGIBLE_STATE_OR_FEEDBACK':c['reason']='NO_SENDABLE_NEW_ANCHOR'
    return dict(version=VERSION,cutoff=cutoff,arm=memory.arm,max_records=max_records,max_bytes=max_bytes,
        conservative_input_token_upper=used,estimate='UTF8 byte upper bound for evidence array only; final wire preflight remains mandatory',
        selected_ids=chosen,candidates=candidates,mechanism_established=False)
