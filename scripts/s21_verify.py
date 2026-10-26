"""Reproduce S21 acceptance locally; no provider or sealed task access."""
import hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/s21_selective_experience_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 inputs=json.loads((OUT/'input_hashes.json').read_text())
 assert all(sha(ROOT/p)==v for p,v in inputs.items()),'historical input changed'
 with (OUT/'test_results.txt').open('w') as log:
  subprocess.run([sys.executable,'-m','unittest','test_s21_selective_experience','test_s20_repair_stream','test_s20_mechanism_stream','-v'],cwd=ROOT/'scripts',stdout=log,stderr=subprocess.STDOUT,check=True)
 names=['audit.json','input_hashes.json','experience_card.json','replay.json','replay_summary.json','experiment_draft.json']
 snapshots=[];start=time.monotonic()
 for _ in range(2):
  for script in ['s21_audit.py','s21_selective_experience.py','s21_protocol_draft.py']:
   subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
  snapshots.append({name:sha(OUT/name) for name in names})
 assert snapshots[0]==snapshots[1],'nondeterministic replay'
 assert all(sha(ROOT/p)==v for p,v in inputs.items()),'historical input changed'
 verify=dict(replays_identical=True,output_sha256=snapshots[1],original_input_files_verified=len(inputs),original_inputs_unchanged=True,new_model_api_calls=0,worker_calls=0,two_replays_wall_seconds=time.monotonic()-start)
 (OUT/'verification.json').write_text(json.dumps(verify,indent=2)+'\n')
 tracked=subprocess.check_output(['git','ls-files','FlowEvo/src/failure_evo','scripts'],cwd=ROOT,text=True).splitlines()
 paths={ROOT/p for p in tracked if p.endswith('.py')}
 paths.update((ROOT/'scripts').glob('*s21*.py'));paths.add(ROOT/'FlowEvo/src/failure_evo/selective_experience.py')
 manifest=dict(base_commit='86edbb90cd4e61c5a87722652bc0b453a2d3f42b',python=sys.version,python_executable=sys.executable,code_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},new_api_calls=0,scope='Tracked failure_evo/scripts Python sources plus new S21 prototype; no external dataset contents')
 (OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(verify,indent=2))
if __name__=='__main__':main()
