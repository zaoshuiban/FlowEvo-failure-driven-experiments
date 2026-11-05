"""Sealed pool -> independently reviewed packages -> existing three Gates.

No mathematical matcher or oracle synthesis. The reviewer is a trusted host,
never the generator. Missing review remains Shadow; filenames cannot grant rights.
"""
import json,time
from pathlib import Path
import jsonschema
from .contracts import fingerprint
from .evidence import EvidenceStore
from .math_stream import read,save,sha
from .math_stream_learning import ReviewedRelease
from .run_health import RunUnhealthy

VERSION='sealed-math-gate-provider-v1'

class SealedGateProvider:
    def __init__(self,stream,arm):
        self.s,self.arm=stream,arm
        binding=stream.plan['gate_pool_binding']
        if sha(Path(binding['path']))!=binding['sha256']:raise PermissionError('Gate pool drift')
        self.pool=read(binding['path']);self.rows={x['task_id']:x for x in self.pool['cases']}
        if len(self.rows)!=len(self.pool['cases']):raise PermissionError('duplicate Gate identity')
        if len({x['original_id'] for x in self.rows.values()})!=len(self.rows):raise PermissionError('duplicate Gate original')
        if self.pool['origin']!='ORGANIZER_ARCHIVE' and not (stream.engineering and self.pool['origin']=='ENGINEERING_FIXTURE'):raise PermissionError('untrusted oracle origin')
        if not stream.engineering:
            if any(x.get('lineage_id') in (None,'','UNKNOWN') for x in self.rows.values()):raise PermissionError('unknown Gate lineage')
            stream_groups={v.get('lineage_id','UNKNOWN') for v in stream.lineage.values()}
            if stream_groups & {x['lineage_id'] for x in self.rows.values()}:raise PermissionError('online/Gate lineage overlap')
        online={v['source_original_id'] for v in stream.lineage.values()}
        if online & {x['original_id'] for x in self.rows.values()}:raise PermissionError('online/Gate original overlap')
        if {t.task_id for t in stream.tasks}&set(self.rows):raise PermissionError('online/Gate task overlap')
        self.root=stream.path/arm/'private/gate_reviews';self.root.mkdir(parents=True,exist_ok=True)
        self.events=EvidenceStore(self.root/'audit.jsonl')
    def review_path(self,a):return self.root/(a['code_sha256']+'.json')
    def __call__(self,a,cutoff):
        s=self.s;p=self.review_path(a)
        if not p.exists():
            target=self.root/(a['code_sha256']+'.request.json')
            if not target.exists():save(target,dict(version=VERSION,artifact=a,available_after_sequence=cutoff,
                pool_sha256=s.plan['gate_pool_binding']['sha256'],status='INDEPENDENT_HOST_REVIEW_REQUIRED',
                instructions='Review mathematical premises and exact parameter mapping without executing candidate on Gate. Label every pool item, including UNKNOWN; no answers or observed outputs in review. Missing coverage keeps Shadow.'))
            return None
        r=read(p)
        fields={'version','artifact_sha256','pool_sha256','reviewer','review_method','Development','Gate'}
        if set(r)!=fields or r['version']!=VERSION or r['artifact_sha256']!=a['code_sha256'] or r['pool_sha256']!=s.plan['gate_pool_binding']['sha256']:raise PermissionError('review binding/schema')
        if r['reviewer'] not in s.plan['gate_reviewers'] or r['review_method']!='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION':raise PermissionError('untrusted review')
        def labels(items):
            if not isinstance(items,list):raise PermissionError('review list')
            result={}
            for x in items:
                if set(x)!={'task_id','supported','parameters','reason','assumption_quotes'} or x['task_id'] in result:raise PermissionError('review fields/duplicate; no model answers allowed')
                if x['supported'] is not None and type(x['supported']) is not bool:raise PermissionError('support label')
                if not isinstance(x['reason'],str) or not x['reason'].strip() or not isinstance(x['assumption_quotes'],list):raise PermissionError('independent reason required')
                if x['supported'] is True:jsonschema.validate(x['parameters'],json.loads(a['contract']['parameter_schema']))
                elif x['parameters'] is not None:raise PermissionError('unsupported/unknown parameters')
                result[x['task_id']]=x
            return result
        gate=labels(r['Gate']);dev=labels(r['Development'])
        if set(gate)!=set(self.rows):raise PermissionError('whole pool review required, not outcome-selected subset')
        public={t.task_id:t for t in s.tasks[:cutoff]}
        if not set(dev)<=set(public) or not 2<=len(dev)<=12:raise PermissionError('development must be past locked tasks')
        # Host labels cannot bypass the current source lock barrier.
        locked={x['payload']['task_id'] for x in s.arms[self.arm]['states'].records() if x['kind']=='PRIVATE_SCORED' and x['payload']['sequence']<=cutoff and x['payload']['verdict']['status']!='INFRASTRUCTURE_MISSING'}
        if not set(dev)<=locked:raise PermissionError('development not locked/scored')
        source={s.lineage[t]['source_original_id'] for t in a['excluded_task_ids']}
        if source&{x['original_id'] for x in self.rows.values()}:raise PermissionError('source overlap')
        for tid,x in {**dev,**gate}.items():
            problem=self.rows[tid]['problem'] if tid in gate else public[tid].problem
            if any(not isinstance(q,str) or not q or q not in problem for q in x['assumption_quotes']):raise PermissionError('nonpublic premise quote')
            if x['supported'] is True and not x['assumption_quotes']:raise PermissionError('supported case needs public premises')
        old=[x['payload'] for x in self.events.records() if x['kind']=='REVIEW_FROZEN' and x['payload']['artifact_sha256']==a['code_sha256']]
        digest=fingerprint(r)
        if old and old[0]['review_sha256']!=digest:raise PermissionError('review changed after freezing')
        positive=[x['task_id'] for x in self.pool['cases'] if gate[x['task_id']]['supported'] is True]
        negative=[x['task_id'] for x in self.pool['cases'] if gate[x['task_id']]['supported'] is False]
        # Fixed first 2+2 by pool order. Unknown cases never become convenient negatives.
        if len(positive)<2 or len(negative)<2 or not any(x['supported'] is True for x in dev.values()) or not any(x['supported'] is False for x in dev.values()):
            return None
        chosen=positive[:2]+negative[:2]
        def case(tid,x,base):
            return dict(task_id=tid,problem=base['problem'],original_id=base['original_id'],supported=x['supported'],parameters=x['parameters'],answer=base['answer'],
                oracle_sha256=base['oracle_sha256'],reviewer=r['reviewer'],review_status='INDEPENDENT_VERIFIED',available_after_sequence=cutoff,
                semantic_review_sha256=digest,reason=x['reason'])
        dc=[]
        for tid,x in dev.items():
            if x['supported'] is None:continue
            # Private references are read only here, never supplied to Worker/learner.
            ref=s.plan['cumulative_input_bindings']['private_scoring']
            if sha(Path(ref['path']))!=ref['sha256']:raise PermissionError('private reference drift')
            row=next(json.loads(l) for l in Path(ref['path']).read_text().splitlines() if json.loads(l)['task_id']==tid)
            dc.append(case(tid,x,dict(problem=public[tid].problem,original_id=s.lineage[tid]['source_original_id'],answer=row['gold_answer'],oracle_sha256=row.get('oracle_sha256',fingerprint(row)))))
        package=dict(origin=self.pool['origin'],artifact_sha256=a['code_sha256'],Development=dc,Gate=[case(tid,gate[tid],self.rows[tid]) for tid in chosen])
        if not old:self.events.append('REVIEW_FROZEN',dict(artifact_sha256=a['code_sha256'],review_sha256=digest,selected_gate_ids=chosen,package_sha256=fingerprint(package),selection='pool-order first2positive first2negative before candidate Gate execution'),time.time())
        return package

class PoolReviewedRelease(ReviewedRelease):
    """Publish only after actual review+execution. Retry review availability, never requests."""
    def __init__(self,s,arm):
        super().__init__(s,arm,SealedGateProvider(s,arm));self.journal=EvidenceStore(s.path/arm/'private/release_queue.jsonl')
    def attempt(self,a,cutoff,path):
        s=self.stream;path=Path(path)
        done=[r['payload'] for r in self.journal.records() if r['kind']=='RELEASE_COMPLETED' and r['payload']['sha']==a['code_sha256']]
        if done:return done[0]['result']
        history=[r for r in self.journal.records() if r['payload'].get('sha')==a['code_sha256']]
        if history and history[-1]['kind']=='RELEASE_STARTED':raise RunUnhealthy('interrupted Gate requires audit; no replay')
        package=self.packages(a,cutoff)
        if package is None:
            if not any(r['kind']=='RELEASE_PENDING' and r['payload']['sha']==a['code_sha256'] for r in self.journal.records()):self.journal.append('RELEASE_PENDING',dict(sha=a['code_sha256'],artifact=a,path=str(path),created_after=cutoff),time.time())
            return dict(status='SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE',gate_passed=False)
        learner=s.arms[self.arm]['learner']
        if not learner.capacity(cutoff,4*len(package['Gate']),gate=True):return dict(status='SHADOW_GATE_WINDOW_BUDGET_UNAVAILABLE',gate_passed=False)
        # Attribute delayed Gate requests to the window where they actually occur (R accounting).
        target=learner._path(cutoff,'gate-'+a['code_sha256']);target.mkdir(parents=True,exist_ok=True)
        self.journal.append('RELEASE_STARTED',dict(sha=a['code_sha256'],cutoff=cutoff,path=str(target)),time.time())
        result=super().attempt(a,cutoff,target)
        kind='RELEASE_DEFERRED' if result.get('status')=='SHADOW_RELEASE_STAGES_PENDING' else 'RELEASE_COMPLETED'
        self.journal.append(kind,dict(sha=a['code_sha256'],cutoff=cutoff,result=result,path=str(path)),time.time());return result
    def poll(self,cutoff):
        done={r['payload']['sha'] for r in self.journal.records() if r['kind']=='RELEASE_COMPLETED'}
        for r in self.journal.records():
            if r['kind'] in ('RELEASE_PENDING','RELEASE_DEFERRED') and r['payload']['sha'] not in done:
                x=r['payload'];self.attempt(x['artifact'],cutoff,Path(x['path']))
