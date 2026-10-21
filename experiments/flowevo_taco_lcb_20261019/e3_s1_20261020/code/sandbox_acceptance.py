"""Linux-only real process isolation and repair-operator contract checks."""
import hashlib,json,pathlib,sys,tempfile
R=pathlib.Path(__file__).resolve().parents[1];B=R.parent
sys.path.insert(0,str(R/'implementation/FlowEvo/src'));sys.path.insert(0,str(B/'repair_v2d_20261020/code'))
from failure_evo import SandboxOperatorRunner,OperatorCard,Fingerprint,PublicTaskView
from sandbox import Worker
def main():
 root=R/'acceptance';root.mkdir(exist_ok=True);fp=Fingerprint('unit','unit','unit','unit','unit');rows=[]
 with tempfile.TemporaryDirectory(prefix='s1_acceptance_') as directory:
  d=pathlib.Path(directory);source=d/'operator.py';source.write_text('def repair_operator(payload):\n    return {"status":"proposed","diagnostic":payload["task"]["prompt"]}\n')
  def card(p):return OperatorCard('synthetic_acceptance_only','v1','shadow',str(p),hashlib.sha256(p.read_bytes()).hexdigest(),fp,0,evidence_scope='SYNTHETIC_TEST_ONLY',evidence_id='NOT_ADMITTED')
  view=PublicTaskView.project({'task_id':'test','prompt':'public prompt','input_output':{'private':'not visible'}})
  r=SandboxOperatorRunner(Worker).run(card(source),{'task':view.to_dict()},.5);assert r=={'status':'proposed','diagnostic':'public prompt'};rows.append({'check':'actual_sandbox_operator_contract','passed':True,'result':r})
  source.write_text('def repair_operator(payload):\n    while True:\n        pass\n');r=SandboxOperatorRunner(Worker).run(card(source),{},.1);assert r['status']=='error' and r['reason']=='TIME_LIMIT';rows.append({'check':'actual_sandbox_deadline','passed':True,'result':r})
  marker=d/'host_marker';marker.write_text('synthetic host-only marker');probe=d/'probe.py';probe.write_text('def probe(path):\n    try:\n        open(path).read()\n        return False\n    except FileNotFoundError:\n        return True\n')
  with Worker(probe) as w:r=w.call({'mode':'function','function':'probe','args':[str(marker)],'timeout':.5})
  assert r['status']=='OK' and r['value'] is True;rows.append({'check':'host_file_not_mounted_into_worker','passed':True,'result':r})
 out={'status':'PASS','real_sandbox_checks':len(rows),'synthetic_fixture_only':True,'new_model_calls':0,'checks':rows};(R/'sandbox_acceptance.json').write_text(json.dumps(out,indent=2));print('REAL SANDBOX ACCEPTANCE PASS',len(rows))
if __name__=='__main__':main()
