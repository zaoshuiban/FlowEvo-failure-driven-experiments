"""One aggregate relation per event, multiple grounded quotes; no conflict merge."""
from .contracts import canonical
VERSION='evidence-link-v2'
ROLES={'SUPPORTS':'SUPPORT','CONTRADICTS':'COUNTEREXAMPLE','UNRELATED':'UNRELATED','UNCERTAIN':'POSSIBLE'}
class LinkConflict(ValueError):
    def __init__(self,diagnostic):
        self.diagnostic=diagnostic
        super().__init__(canonical(diagnostic))

def cardinality(links):
    seen={}
    for i,link in enumerate(links):
        eid=link.get('evidence_id') if isinstance(link,dict) else None
        if not isinstance(eid,str):raise ValueError('links['+str(i)+'].evidence_id must be string')
        if eid in seen:
            j=seen[eid]
            raise LinkConflict(dict(code='EVENT_RELATION_CARDINALITY',evidence_id=eid,
                paths=['links['+str(j)+']','links['+str(i)+']'],
                relations=[links[j].get('relation'),link.get('relation')],
                instruction='Preserve relevant quotes in quote_spans. Choose ONE aggregate relation, or UNCERTAIN if conflicting; do not discard conflicting evidence.'))
        seen[eid]=i

def receive(link,allowed,path):
    # Explicit legacy shape for saved v1 callers; never collapse repeated records.
    legacy=set(link)=={'evidence_id','relation','reason','evidence_quote','new_information'}
    expected={'evidence_id','relation','reason','quote_spans','new_information'}
    if not legacy and set(link)!=expected:raise ValueError(path+' fields extra='+str(sorted(set(link)-expected))+' missing='+str(sorted(expected-set(link))))
    quotes=[link['evidence_quote']] if legacy else link['quote_spans']
    roles=set(ROLES.values()) if legacy else set(ROLES)
    if link['relation'] not in roles:raise ValueError(path+'.relation unsupported')
    if type(link['new_information']) is not bool:raise ValueError(path+'.new_information must be bool')
    if not isinstance(link['reason'],str) or not link['reason'].strip() or len(link['reason'])>6000:raise ValueError(path+'.reason invalid')
    if not isinstance(quotes,list) or not 1<=len(quotes)<=8:raise ValueError(path+'.quote_spans requires 1..8 quotes')
    for n,q in enumerate(quotes):
        if not isinstance(q,str) or not q.strip() or len(q)>6000 or q not in allowed:
            raise ValueError(path+'.quote_spans['+str(n)+']: ungrounded relation quote')
    return dict(evidence_id=link['evidence_id'],relation=link['relation'] if legacy else ROLES[link['relation']],
        reason=link['reason'],quote_spans=list(quotes),new_information=link['new_information'],
        input_schema='evidence-link-v1' if legacy else VERSION,model_relation=link['relation'])

INSTRUCTIONS=('Each cluster has at most ONE link per evidence_id. Each link has evidence_id, relation '
 '(SUPPORTS/CONTRADICTS/UNRELATED/UNCERTAIN), reason, quote_spans (1..8 exact public substrings), new_information (boolean). '
 'Multiple quotes from one event belong to the same quote_spans array, not repeated links. '
 'Choose one aggregate relation; when quotes conflict or cannot establish a single direction, use UNCERTAIN and explain the conflict. '
 'Never delete conflicting quotes merely to obtain acceptance. Relations remain unverified hypotheses. ')

def validate_revision(before,after):
    """Relation repair cannot silently change hypothesis or discard quoted evidence."""
    if before.get('descriptions')!=after.get('descriptions') or len(before.get('clusters',[]))!=len(after.get('clusters',[])):
        raise ValueError('relation revision changed descriptions/cluster count')
    for old,new in zip(before['clusters'],after['clusters']):
        if {k:v for k,v in old.items() if k!='links'}!={k:v for k,v in new.items() if k!='links'}:
            raise ValueError('relation revision changed hypothesis or identity')
        cardinality(new['links'])
        ids={x['evidence_id'] for x in old['links']}
        if ids!={x['evidence_id'] for x in new['links']}:raise ValueError('relation revision changed evidence set')
        for link in new['links']:
            required=[q for x in old['links'] if x['evidence_id']==link['evidence_id'] for q in x.get('quote_spans',[x.get('evidence_quote')])]
            if any(q not in link.get('quote_spans',[]) for q in required):raise ValueError('relation revision discarded quote')
