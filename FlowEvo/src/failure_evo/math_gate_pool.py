"""Sealed pool -> independently reviewed packages -> existing three Gates.

No mathematical matcher or oracle synthesis. The reviewer is a trusted host,
never the generator. Missing review remains Shadow; filenames cannot grant rights.
"""
import base64,binascii,json,subprocess,tempfile,time
from pathlib import Path
import jsonschema
from .contracts import fingerprint
from .evidence import EvidenceStore
from .math_stream import read,save,sha
from .math_stream_learning import ReviewedRelease
from .run_health import RunUnhealthy
from .operator_contract import candidate_identity

VERSION='sealed-math-gate-provider-v1'
CONTRACT_VERSION='sealed-math-gate-provider-v2'
AUTOMATED_GATE='AUTOMATED_GATE'
AUTO_VALIDATOR='split-exact-rational-v1'

def review_version(a):return CONTRACT_VERSION if 'operator_contract' in a else VERSION

def event_identity(payload):
    if 'candidate_version' in payload:return payload['candidate_version']
    if 'operator_contract' in payload.get('artifact',{}):return None
    # Legacy code-only events remain scoped to legacy artifacts.
    return payload.get('sha',payload.get('artifact_sha256'))


def review_signature_message(plan, arm, identity, review):
    """Bind the signed labels to their exact frozen run, arm and candidate."""
    return fingerprint(dict(
        domain='flowevo-independent-review-v1', plan_sha256=fingerprint(plan),
        arm=arm, candidate_version=identity, review=review,
    )).encode('ascii')


def is_ed25519_public_key(key):
    if not isinstance(key, str):
        return False
    lines = key.strip().splitlines()
    if len(lines) != 3 or lines[0] != '-----BEGIN PUBLIC KEY-----' or lines[2] != '-----END PUBLIC KEY-----':
        return False
    try:
        der = base64.b64decode(lines[1], validate=True)
    except ValueError:
        return False
    # RFC 8410 SubjectPublicKeyInfo for a 32-byte Ed25519 public key.
    return len(der) == 44 and der.startswith(bytes.fromhex('302a300506032b6570032100'))


def verify_review_signature(plan, arm, identity, review, encoded):
    key = plan.get('gate_reviewer_public_keys', {}).get(review['reviewer'])
    if not is_ed25519_public_key(key) or not isinstance(encoded, str):
        raise PermissionError('independent review signing key or signature missing')
    try:
        signature = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise PermissionError('invalid independent review signature encoding') from exc
    if len(signature) != 64:
        raise PermissionError('invalid Ed25519 signature length')
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'key.pem').write_text(key, encoding='ascii')
        (root / 'message').write_bytes(review_signature_message(plan, arm, identity, review))
        (root / 'signature').write_bytes(signature)
        result = subprocess.run(
            ['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(root / 'key.pem'),
             '-rawin', '-in', str(root / 'message'), '-sigfile', str(root / 'signature')],
            capture_output=True, timeout=5, check=False,
        )
    if result.returncode:
        raise PermissionError('invalid independent review signature')


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
    def review_path(self,a):return self.root/(candidate_identity(a)+'.json')
    def _review(self,a,cutoff):
        s=self.s;identity=candidate_identity(a);p=self.review_path(a)
        signed = bool(s.plan.get('gate_reviewer_public_keys')) or (not s.engineering and 'operator_contract' in a)
        if not p.exists():
            target=self.root/(identity+'.request.json')
            if not target.exists():save(target,dict(version=review_version(a),candidate_version=identity,artifact=a,available_after_sequence=cutoff,
                pool_sha256=s.plan['gate_pool_binding']['sha256'],status='INDEPENDENT_HOST_REVIEW_REQUIRED',
                instructions='Review mathematical premises and exact parameter mapping without executing candidate on Gate. Label every pool item, including UNKNOWN; no answers or observed outputs in review. Missing coverage keeps Shadow.'))
            return None
        r=read(p)
        signed_record = r
        signature = r.get('signature')
        if signed:
            r = {k: v for k, v in r.items() if k != 'signature'}
        fields={'version','artifact_sha256','pool_sha256','reviewer','review_method','Development','Gate'}
        if 'operator_contract' in a:fields.add('candidate_version')
        if set(r)!=fields or r.get('candidate_version',identity)!=identity or r['version']!=review_version(a) or r['artifact_sha256']!=a['code_sha256'] or r['pool_sha256']!=s.plan['gate_pool_binding']['sha256']:raise PermissionError('review binding/schema')
        if r['reviewer'] not in s.plan['gate_reviewers'] or r['review_method']!='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION':raise PermissionError('untrusted review')
        if signed:
            verify_review_signature(s.plan, self.arm, identity, r, signature)
        return r, signed_record

    def __call__(self,a,cutoff):
        s=self.s
        identity=candidate_identity(a)
        prior=[x['payload'] for x in self.events.records() if x['kind']=='REVIEW_FROZEN' and event_identity(x['payload'])==identity]
        if prior and s.plan.get('gate_mode')==AUTOMATED_GATE:
            if cutoff<prior[0]['cutoff']:
                raise PermissionError('automatic Gate cutoff precedes frozen review')
            cutoff=prior[0]['cutoff']
        reviewed=self._review(a,cutoff)
        if reviewed is None:
            return None
        r,signed_record=reviewed
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
        old=prior
        digest=fingerprint(signed_record)
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
        if 'operator_contract' in a:package['candidate_version']=identity
        if not old:self.events.append('REVIEW_FROZEN',dict(candidate_version=identity,artifact_sha256=a['code_sha256'],review_sha256=digest,selected_gate_ids=chosen,cutoff=cutoff,package_sha256=fingerprint(package),selection='pool-order first2positive first2negative before candidate Gate execution'),time.time())
        return package


class AutomatedGateProvider(SealedGateProvider):
    """Use host-frozen mappings and organizer answers with the existing SplitRunner."""

    def __init__(self, stream, arm):
        from code_math.private_math_scoring import normalized

        super().__init__(stream, arm)
        if stream.plan.get('automatic_gate_validator') != AUTO_VALIDATOR:
            raise PermissionError('trusted automatic Gate validator required')
        if stream.plan.get('stop_for_gate_review') or stream.plan.get('operator_contract_shadow') != 'pre-score-one-candidate-v1':
            raise PermissionError('automated Gate requires existing Shadow policy and no manual pause')
        self.profiles = self.pool.get('automated_profiles')
        if not isinstance(self.profiles, dict) or not self.profiles:
            raise PermissionError('frozen automated applicability and parameter profiles required')
        if not stream.engineering and any(
            stream.lineage[t.task_id].get('source_identity_verified') is not True
            or stream.lineage[t.task_id].get('prior_exposure') is not False
            or stream.lineage[t.task_id].get('source_original_id') in (None, '', 'UNKNOWN')
            or stream.lineage[t.task_id].get('lineage_id') in (None, '', 'UNKNOWN')
            for t in stream.tasks
        ):
            raise PermissionError('verified online originals, lineages and exposure required')
        public = {t.task_id:t.problem for t in stream.tasks}
        ref = stream.plan['cumulative_input_bindings']['private_scoring']
        ref_path = Path(ref['path'])
        if sha(ref_path) != ref['sha256']:
            raise PermissionError('private reference drift')
        refs = {row['task_id']:row for row in map(json.loads,ref_path.read_text().splitlines())}
        for case in self.rows.values():
            if normalized(case['answer'])[0] != 'rational' or not case.get('oracle_sha256'):
                raise PermissionError('automatic Gate requires exact rational organizer answers')
            if not stream.engineering and (not case.get('source') or not case.get('answer_source')
                                           or case.get('prior_exposure') is not False):
                raise PermissionError('Gate provenance and exposure evidence required')
        for key, profile in self.profiles.items():
            if len(key)!=64 or any(c not in '0123456789abcdef' for c in key) or set(profile)!={'Development','Gate'}:
                raise PermissionError('invalid automated profile identity')
            for role, statements in (('Development',public),('Gate',{k:v['problem'] for k,v in self.rows.items()})):
                labels = profile[role]
                allowed = {x['task_id'] for x in labels}
                if len(allowed)!=len(labels) or not allowed<=statements.keys() or (role=='Gate' and allowed!=statements.keys()):
                    raise PermissionError('automated profile task coverage')
                needed = 2 if role=='Gate' else 1
                if sum(x['supported'] is True for x in labels)<needed or sum(x['supported'] is False for x in labels)<needed:
                    raise PermissionError('insufficient automated positive/negative coverage')
                for label in labels:
                    tid=label['task_id']
                    if (set(label)!={'task_id','supported','parameters','reason','assumption_quotes','problem_sha256'}
                            or label['problem_sha256']!=fingerprint(statements[tid])
                            or (label['supported'] is not None and type(label['supported']) is not bool)
                            or (label['supported'] is True and not isinstance(label['parameters'],dict))
                            or (label['supported'] is not True and label['parameters'] is not None)
                            or not isinstance(label['reason'],str) or not label['reason'].strip()
                            or not isinstance(label['assumption_quotes'],list)
                            or any(not isinstance(q,str) or not q or q not in statements[tid] for q in label['assumption_quotes'])
                            or (label['supported'] is True and not label['assumption_quotes'])):
                        raise PermissionError('invalid frozen automatic labels')
                    if role=='Development' and (refs[tid]['problem_sha256']!=label['problem_sha256']
                                                or normalized(refs[tid]['gold_answer'])[0]!='rational'):
                        raise PermissionError('automatic SOURCE reference not bound or not exact rational')

    def _review(self, artifact, cutoff):
        binding=self.s.plan['gate_pool_binding']
        if sha(Path(binding['path']))!=binding['sha256']:
            raise PermissionError('Gate pool drift')
        from .operator_contract import require_stages

        if 'operator_contract' not in artifact:
            return None
        profile = self.profiles.get(fingerprint(artifact['contract']))
        if profile is None:
            return None
        try:
            require_stages(self.s.arms[self.arm]['registry'],artifact,('STATIC_SAFETY',))
        except PermissionError:
            return None
        past={t.task_id for t in self.s.tasks[:cutoff]}
        if not set(artifact['excluded_task_ids'])<=past:
            return None
        scored={r['payload']['task_id'] for r in self.s.arms[self.arm]['states'].records()
                if r['kind']=='PRIVATE_SCORED' and r['payload']['sequence']<=cutoff
                and r['payload']['verdict']['status']!='INFRASTRUCTURE_MISSING'}
        development=[row for row in profile['Development'] if row['task_id'] in past & scored]
        positive_sources={self.s.lineage[row['task_id']]['source_original_id'] for row in development
                          if row['supported'] is True and row['task_id'] in artifact['excluded_task_ids']}
        required=set(artifact.get('source_original_ids',[]))
        if (not required or not required<=positive_sources or not 2<=len(development)<=12
                or not any(row['supported'] is False for row in development)):
            return None
        schema=json.loads(artifact['contract']['parameter_schema'])
        labels={}
        for role, rows in (('Development',development),('Gate',profile['Gate'])):
            labels[role]=[{k:v for k,v in x.items() if k!='problem_sha256'} for x in rows]
            if any(x['supported'] is True and not jsonschema.Draft202012Validator(schema).is_valid(x['parameters'])
                   for x in labels[role]):
                return None
        record=dict(**labels,reviewer=AUTO_VALIDATOR,candidate_version=candidate_identity(artifact),
                    pool_sha256=self.s.plan['gate_pool_binding']['sha256'])
        return record,record

class PoolReviewedRelease(ReviewedRelease):
    """Publish only after actual review+execution. Retry review availability, never requests."""
    def __init__(self,s,arm):
        provider=AutomatedGateProvider if s.plan.get('gate_mode')==AUTOMATED_GATE else SealedGateProvider
        super().__init__(s,arm,provider(s,arm));self.journal=EvidenceStore(s.path/arm/'private/release_queue.jsonl')
    def attempt(self,a,cutoff,path):
        s=self.stream;path=Path(path);identity=candidate_identity(a)
        history=[r for r in self.journal.records() if event_identity(r['payload'])==identity]
        done=[r['payload'] for r in history if r['kind']=='RELEASE_COMPLETED']
        if done:return done[0]['result']
        if history and history[-1]['kind']=='RELEASE_STARTED':raise RunUnhealthy('interrupted Gate requires audit; no replay')
        automatic=s.plan.get('gate_mode')==AUTOMATED_GATE
        if automatic and any(r['kind']=='RELEASE_STARTED' and event_identity(r['payload'])!=identity
                             for r in self.journal.records()):
            return dict(status='BLOCKED_AUTOMATED_GATE_POOL_CONSUMED',gate_passed=False)
        package=self.packages(a,cutoff)
        if package is None:
            if automatic:
                self.journal.append('AUTOMATED_GATE_UNVERIFIED',dict(candidate_version=identity,cutoff=cutoff),time.time())
                return dict(status='UNVERIFIED_AUTOMATED_GATE_EVIDENCE',gate_passed=False)
            if not any(r['kind']=='RELEASE_PENDING' for r in history):
                self.journal.append('RELEASE_PENDING',dict(candidate_version=identity,sha=a['code_sha256'],artifact=a,path=str(path),created_after=cutoff),time.time())
            return dict(status='SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE',gate_passed=False)
        learner=s.arms[self.arm]['learner']
        if not learner.capacity(cutoff,4*len(package['Gate']),gate=True):return dict(status='SHADOW_GATE_WINDOW_BUDGET_UNAVAILABLE',gate_passed=False)
        started=next((r['payload'] for r in history if r['kind']=='RELEASE_STARTED'),None)
        target=Path(started['path']) if automatic and started else learner._path(cutoff,'gate-'+identity)
        target.mkdir(parents=True,exist_ok=True)
        self.journal.append('RELEASE_STARTED',dict(candidate_version=identity,sha=a['code_sha256'],cutoff=cutoff,path=str(target)),time.time())
        result=super().attempt(a,cutoff,target)
        kind='RELEASE_DEFERRED' if result.get('status')=='SHADOW_RELEASE_STAGES_PENDING' else 'RELEASE_COMPLETED'
        self.journal.append(kind,dict(candidate_version=identity,sha=a['code_sha256'],artifact=a,cutoff=cutoff,result=result,path=str(path)),time.time())
        return result
    def pending_records(self):
        rows=self.journal.records()
        done={event_identity(r['payload']) for r in rows if r['kind']=='RELEASE_COMPLETED'}
        pending={}
        for r in rows:
            if r['kind'] not in ('RELEASE_PENDING','RELEASE_DEFERRED'):continue
            x=r['payload'];identity=event_identity(x)
            if identity is None or identity in done:continue
            if 'artifact' not in x:
                if identity not in pending:raise RunUnhealthy('incomplete legacy deferred release; audit required')
                x=dict(pending[identity],**x)
            if candidate_identity(x['artifact'])!=identity:raise PermissionError('queued artifact/version mismatch')
            pending[identity]=x
        return list(pending.values())
    def poll(self,cutoff):
        for x in self.pending_records():self.attempt(x['artifact'],cutoff,Path(x['path']))
