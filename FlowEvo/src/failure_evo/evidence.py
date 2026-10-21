"""Append-only evidence state with publication time and distinct-source gates."""
import hashlib,json,pathlib,threading,math,difflib
from .contracts import canonical,fingerprint

REQUIRED_FILES=('legal_case','oracle','original_code','patched_code','original_run','minimal_patch','patched_run','review')
class EvidenceStore:
    def __init__(self,path):self.path=pathlib.Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.lock=threading.Lock()
    def records(self):
        rows=[];previous='0'*64
        if not self.path.exists():return rows
        for text in self.path.read_text().splitlines():
            row=json.loads(text);payload={k:v for k,v in row.items() if k!='record_hash'}
            if row['previous_hash']!=previous or fingerprint(payload)!=row['record_hash']:raise ValueError('evidence chain changed')
            rows.append(row);previous=row['record_hash']
        return rows
    def append(self,kind,payload,at):
        with self.lock:
            if not isinstance(at,(int,float)) or isinstance(at,bool) or not math.isfinite(at):raise ValueError('finite timestamp required')
            rows=self.records()
            if rows and at<rows[-1]['at']:raise ValueError('append timestamp precedes stored record')
            row={'kind':kind,'payload':payload,'at':float(at),'previous_hash':rows[-1]['record_hash'] if rows else '0'*64};row['record_hash']=fingerprint(row)
            with self.path.open('a') as f:f.write(canonical(row)+'\n');f.flush()
            return row
    def visible(self,at):return [r for r in self.records() if r['at']<=at]

class MechanismStore:
    def __init__(self,path,evidence_root=None):self.events=EvidenceStore(path);self.evidence_root=pathlib.Path(evidence_root) if evidence_root is not None else pathlib.Path(path).parent
    def certify(self,witness,at):
        if witness.get('synthetic') or witness.get('purpose')!='HISTORICAL_FUNCTIONAL_FAILURE':raise ValueError('synthetic/engineering fixture cannot certify a mechanism')
        if at<witness['observed_at']:raise ValueError('certification before observation')
        files=witness.get('files',{});loaded={}
        for key in REQUIRED_FILES:
            p=self.evidence_root/pathlib.Path(files[key]['path'])
            if hashlib.sha256(p.read_bytes()).hexdigest()!=files[key]['sha256']:raise ValueError('evidence artifact hash mismatch')
            if key in ['original_code','patched_code']:loaded[key]=p.read_text()
            elif key!='minimal_patch':loaded[key]=json.loads(p.read_text())
            elif not p.read_text().strip():raise ValueError('empty counterfactual')
        legal,oracle,run,patched,review=[loaded[k] for k in ['legal_case','oracle','original_run','patched_run','review']]
        if not legal.get('legal_verified') or legal.get('visibility')!='public':raise ValueError('legal public witness required')
        if not oracle.get('independent') or not oracle.get('method'):raise ValueError('independent oracle required')
        if run.get('status') not in ['WRONG_ANSWER','RUNTIME_ERROR','TIME_LIMIT']:raise ValueError('no functional failure')
        if run.get('code_sha256')!=witness['code_sha256']:raise ValueError('original source mismatch')
        if hashlib.sha256(loaded['original_code'].encode()).hexdigest()!=witness['code_sha256']:raise ValueError('original source file differs')
        if loaded['original_code']==loaded['patched_code']:raise ValueError('counterfactual changed no code')
        if (self.evidence_root/pathlib.Path(files['minimal_patch']['path'])).read_text()!=''.join(difflib.unified_diff(loaded['original_code'].splitlines(True),loaded['patched_code'].splitlines(True),fromfile='original.py',tofile='patched.py')):raise ValueError('minimal patch not linked to source pair')
        if oracle.get('case_id')!=legal.get('case_id') or run.get('case_id')!=legal.get('case_id'):raise ValueError('case linkage differs')
        if run.get('expected')!=oracle.get('expected'):raise ValueError('oracle/run expected differs')
        if run['status']=='WRONG_ANSWER' and run.get('actual')==oracle.get('expected'):raise ValueError('no observable mismatch')
        if run['status']=='RUNTIME_ERROR' and not run.get('exception_class'):raise ValueError('missing exception evidence')
        if patched.get('status')!='PASS' or patched.get('tests_passed',0)<1 or not patched.get('original_witness_passed') or patched.get('case_id')!=legal.get('case_id') or patched.get('code_sha256')!=hashlib.sha256(loaded['patched_code'].encode()).hexdigest():raise ValueError('counterfactual not verified or source linkage differs')
        if run['status']=='TIME_LIMIT' and not run.get('resource_calibrated'):raise ValueError('timeout without resource calibration')
        if not review.get('mechanism_verified') or not review.get('violated_invariant') or not review.get('reviewer'):raise ValueError('semantic review absent')
        record={k:v for k,v in witness.items()};record['certified_at']=at
        return self.events.append('WITNESS_CERTIFIED',record,at)
    def supports(self,mechanism,at):
        witnesses=[r['payload'] for r in self.events.visible(at) if r['kind']=='WITNESS_CERTIFIED' and r['payload']['mechanism_id']==mechanism]
        by_problem={w['problem_id']:w for w in witnesses}
        independent=[w for w in by_problem.values() if w.get('provenance_reviewed') is True]
        return {'distinct_problems':len(by_problem),'reviewed_provenance_groups':len({w['provenance_group_id'] for w in independent}),
                'all_provenance_reviewed':len(independent)==len(by_problem),'witness_ids':[w['witness_id'] for w in by_problem.values()]}
    def publish(self,mechanism,at):
        counts=self.supports(mechanism,at)
        if counts['distinct_problems']<3 or counts['reviewed_provenance_groups']<2 or not counts['all_provenance_reviewed']:raise ValueError('cross-task support gate not met')
        return self.events.append('MECHANISM_PUBLISHED',{'mechanism_id':mechanism,'support':counts,'published_at':at,'state':'CROSS_TASK_SUPPORTED_NOT_HEADROOM_TESTED'},at)
    def record_headroom(self,mechanism,trial_file,at):
        records=self.events.visible(at)
        if not any(r['kind']=='MECHANISM_PUBLISHED' and r['payload']['mechanism_id']==mechanism for r in records):raise ValueError('mechanism cross-task gate not passed')
        p=pathlib.Path(trial_file);trial=json.loads(p.read_text())
        if trial.get('role')!='DEVELOPMENT_HEADROOM' or trial.get('mechanism_id')!=mechanism or not trial.get('frozen_initial_state') or not trial.get('paired_budget_verified'):raise ValueError('invalid headroom experiment')
        problems=trial['problems'];difficult=set();benefit=set()
        for row in problems:
            if len(row['G'])!=3 or len(row['D_star'])!=3 or not all(type(x) is bool for x in row['G']+row['D_star']):raise ValueError('three independent repeats per arm required')
            if sum(row['G'])<=1:difficult.add(row['problem_id'])
            if sum(row['D_star'])>sum(row['G']):benefit.add(row['problem_id'])
        passed=len(difficult)>=2 and len(benefit)>=2
        return self.events.append('HEADROOM_REVIEWED',{'mechanism_id':mechanism,'trial_path':str(p.resolve()),'trial_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'state':'HEADROOM_PASSED_PILOT_ONLY' if passed else 'NO_HEADROOM_DEMONSTRATED','passed':passed},at)
