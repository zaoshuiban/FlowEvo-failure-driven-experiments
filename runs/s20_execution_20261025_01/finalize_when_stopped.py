"""Offline-only completion watcher. It cannot send model requests or resume online work."""
import pathlib,json,time,subprocess,sys
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1]
while True:
 state=json.loads((P/'execution_status.json').read_text())
 if state['status']!='RUNNING':break
 time.sleep(5)
if state['status']=='ONLINE_COMPLETE':
 with (P/'final_evaluation.log').open('w') as log:rc=subprocess.call([sys.executable,str(P/'final_evaluation.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 if rc:(P/'final_evaluation_failure.json').write_text(json.dumps(dict(status='FAILED',exit_code=rc,no_retry=True)))
with (P/'report.log').open('w') as log:rc=subprocess.call([sys.executable,str(P/'report.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
print('OFFLINE_FINALIZATION_EXIT',rc,flush=True)
