"""Opt-in cumulative stream: old StreamRuntime and historical runs remain untouched."""
import fcntl,time
from .math_stream import StreamRuntime,ARMS,save
from .math_cumulative_learning import CumulativeLearner
from .contracts import fingerprint
from .run_health import RunUnhealthy

DEFAULTS=dict(version='math-cumulative-v2-dual-assessment',comparison='workflow',paid_api_authorized=False,
              association_batch=3,retrieval_limit=6,max_association_jobs=20,max_generation_jobs=6,
              bundle_bytes=22000,wire_upper=65536,output_upper=8192,paired_packs=[])

def validate_config(cfg,tasks):
    if set(cfg)!=set(DEFAULTS) or cfg['version']!=DEFAULTS['version'] or cfg['comparison'] not in ('workflow','paired_information') or type(cfg['paid_api_authorized']) is not bool:raise ValueError('frozen cumulative config')
    for k,lo,hi in [('association_batch',1,6),('retrieval_limit',2,8),('max_association_jobs',1,200),('max_generation_jobs',1,200),('bundle_bytes',2000,30000),('wire_upper',4096,65536),('output_upper',512,8192)]:
        if type(cfg[k]) is not int or not lo<=cfg[k]<=hi:raise ValueError('budget/config '+k)
    if cfg['comparison']=='workflow' and cfg['paired_packs']:raise ValueError('workflow selection cannot pretend paired')
    positions={t['task_id']:i for i,t in enumerate(tasks,1)};seen=set();boundaries=set()
    for p in cfg['paired_packs']:
        if set(p)!={'after_sequence','task_ids'} or type(p['after_sequence']) is not int or not 0<p['after_sequence']<len(tasks) or p['after_sequence'] in boundaries:raise ValueError('paired boundary')
        if not isinstance(p['task_ids'],list) or not 1<=len(p['task_ids'])<=6 or len(set(p['task_ids']))!=len(p['task_ids']):raise ValueError('paired packet')
        if any(i not in positions or positions[i]>p['after_sequence'] or i in seen for i in p['task_ids']):raise ValueError('future/duplicate paired task')
        seen.update(p['task_ids']);boundaries.add(p['after_sequence'])
    if cfg['comparison']=='paired_information' and not cfg['paired_packs']:raise ValueError('predeclared outcome-independent paired packs required')

class CumulativeStream(StreamRuntime):
    def __init__(self,*args,learning_sender_factory=None,release_factory=None,**kwargs):
        # Constructors may be called positionally by existing entry points.
        plan=args[1] if len(args)>1 else kwargs['plan'];tasks=args[2] if len(args)>2 else kwargs['tasks']
        validate_config(plan['cumulative'],tasks)
        if 'learner_factory' in kwargs:raise TypeError('use learning_sender_factory/release_factory')
        if plan.get('continuation_binding'):
            from .math_continuation import inherited_budget_factory
            if 'budget_factory' in kwargs:raise TypeError('continuation owns inherited budget factory')
            path=args[0] if args else kwargs['path']
            kwargs['budget_factory']=inherited_budget_factory(path,plan)
        def factory(s,a):return CumulativeLearner(s,a,sender=learning_sender_factory(a) if learning_sender_factory else None,release=release_factory(s,a) if release_factory else None)
        super().__init__(*args,learner_factory=factory,**kwargs)
    def run(self,*,stop_after_window=None):
        with (self.path/'stream.lock').open('a') as f:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);self.health()
            completed=[r['payload']['sequence'] for r in self.events.records() if r['kind']=='CUMULATIVE_BOUNDARY_COMPLETED']
            if completed and max(completed)<len(self.tasks):
                for arm in ('T','F'):
                    release=self.arms[arm]['learner'].release
                    if hasattr(release,'poll'):release.poll(max(completed))
            if self._awaiting_reviews():return
            for seq,task in enumerate(self.tasks,1):
                if any(r['kind']=='CUMULATIVE_BOUNDARY_COMPLETED' and r['payload']['sequence']==seq for r in self.events.records()):continue
                locks={}
                order=ARMS[(seq-1)%4:]+ARMS[:(seq-1)%4]
                for arm in order:
                    self.health()
                    if self.arms[arm].get('contract_shadow'):self.arms[arm]['contract_shadow'].observe(task,seq)
                    locks[arm]=self.solve(arm,task,seq)
                verdicts={}
                for arm in ARMS:
                    a=self.arms[arm];v=a['scorer'].score(task,locks[arm]);verdicts[arm]=v
                    self.emit_once(a['states'],'PRIVATE_SCORED',f'{arm}/{seq}/{task.task_id}',dict(task_id=task.task_id,sequence=seq,verdict=v))
                    if a['router'] and any(r['kind']=='MATH_ROUTER_EXECUTED' and r['payload']['task_id']==task.task_id for r in a['registry'].events.records()):
                        original=self.lineage[task.task_id]['source_original_id']
                        if original=='UNKNOWN':raise PermissionError('unknown original cannot certify reuse')
                        a['router'].record_feedback(task,locks[arm],v,controller=a['controller'],scorer=a['scorer'].events,original_id=original)
                if self.plan.get('operator_contract_shadow'):
                    for arm in ('T','F'):
                        self.arms[arm]['contract_shadow'].finalize(task,locks[arm])
                        self.arms[arm]['learner'].release.poll_contract(seq)
                self.fault('after_scoring',None,seq)
                for arm in ('T','F'):
                    learner=self.arms[arm]['learner'];learner.ingest(task,locks[arm],verdicts[arm],seq);learner.boundary(seq)
                if seq%self.plan['window']==0 or seq==len(self.tasks):
                    for arm in ('T','F'):self.arms[arm]['learner'].learn(seq)
                    for a in self.arms.values():self.emit_once(a['states'],'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    self.emit_once(self.events,'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                self.emit_once(self.events,'CUMULATIVE_BOUNDARY_COMPLETED',str(seq),dict(sequence=seq))
                missing=[]
                if self.plan.get('continuation_binding'):
                    from .math_stream import read
                    missing=read(self.path/'continuation.json')['missing_sequences']
                save(self.path/'progress.json',dict(last_sequence=seq,completed_comparable_tasks=seq-len([i for i in missing if i<=seq]),missing_sequences=missing,
                    status=('COMPLETED_WITH_MISSING' if missing else 'COMPLETED') if seq==len(self.tasks) else 'RUNNING'))
                print(f'Task {seq}/{len(self.tasks)} completed in G/T/F/R; cumulative learning boundary saved',flush=True)
                if (seq%self.plan['window']==0 or seq==len(self.tasks)) and self._awaiting_reviews():return
                if stop_after_window==seq:return
            missing=[]
            if self.plan.get('continuation_binding'):
                from .math_stream import read
                missing=read(self.path/'continuation.json')['missing_sequences']
            self.emit_once(self.events,'STREAM_COMPLETED','complete',dict(tasks=len(self.tasks)-len(missing),missing_sequences=missing,paid_api=not self.engineering))

    def _awaiting_reviews(self):
        if not self.plan.get('stop_for_gate_review',False):return False
        from .math_stream import read
        progress=self.path/'progress.json'
        if progress.exists() and read(progress).get('last_sequence',0)>=len(self.tasks):return False
        pending=[]
        for arm in ('T','F'):
            release=self.arms[arm]['learner'].release
            if not hasattr(release,'journal'):continue
            done={r['payload']['sha'] for r in release.journal.records() if r['kind']=='RELEASE_COMPLETED'}
            for r in release.journal.records():
                if r['kind']=='RELEASE_PENDING' and r['payload']['sha'] not in done:
                    path=release.packages.review_path(r['payload']['artifact'])
                    if not path.exists():pending.append(str(path))
        if not pending:return False
        from .math_stream import read
        p=self.path/'progress.json';prior=read(p) if p.exists() else {}
        save(p,dict(prior,status='INDEPENDENT_REVIEW_REQUIRED',review_files=pending,paid_requests_paused=True))
        return True
