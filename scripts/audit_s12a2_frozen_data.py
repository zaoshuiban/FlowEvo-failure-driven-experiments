"""Verify copied public samples and ancestry pins, without executing programs."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/s12a2_20261021_01'
DATA=RUN/'data'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target=RUN/'data_audit.json'
    if target.exists():raise FileExistsError('preserve previous audit')
    manifest=json.loads((DATA/'data_roles.json').read_text())
    archive={r['path']:r['sha256'] for r in json.loads((ROOT/'datasets/task_manifest.json').read_text())}
    results=[]
    for role in ('discovery','design'):
        for item in manifest[role]['items']:
            path='data/tasks/'+item['problem_id']+'.json'
            task_path=ROOT/'datasets/extracted'/path;assert sha(task_path)==archive[path]==item['original_task_sha256']
            checkpoint_path=DATA/item['checkpoint_file'];assert sha(checkpoint_path)==item['checkpoint_sha256']
            checkpoint=json.loads(checkpoint_path.read_text());task=json.loads(task_path.read_text())
            assert checkpoint['task_public']['prompt']==task['prompt']
            prompt=' '.join(task['prompt'].split())
            for case in checkpoint['public_cases']:
                assert ' '.join(case['input'].split()) in prompt
                assert ' '.join(case['expected'].split()) in prompt
                assert case['comparison']=='whitespace_token_exact'
            assert all(sha(ROOT/e['source_path'])==e['sha256'] for e in checkpoint['candidate_ledger'])
            results.append(dict(role=role,problem_id=item['problem_id'],public_sample_count=len(checkpoint['public_cases']),
                artifact_and_prompt_hashes='PASS',reference='public statement samples, not independent correctness proof',
                candidate_execution='NOT_RUN',visibility_at_historical_event='public samples existed; executed public feedback unavailable'))
    design=json.loads((DATA/'taco_0226.checkpoint.json').read_text())
    normal=copy.deepcopy(design);normal.update(checkpoint_id='taco_0226:l1',current=design['candidate_ledger'][0],candidate_ledger=design['candidate_ledger'][:1],expected_behavior='decline')
    unavailable=copy.deepcopy(design);unavailable.update(checkpoint_id='engineering:no-public-checker',public_cases=[],expected_behavior='decline',historical_checkpoint=False,engineering_only=True)
    (DATA/'development_regression_checks.json').write_text(json.dumps(dict(role='design_only_not_independent_regression',checkpoints=[normal,unavailable]),ensure_ascii=False,indent=2)+'\n')
    target.write_text(json.dumps(dict(status='PUBLIC_SOURCE_PINS_PASS_INDEPENDENCE_BLOCKED',rows=results,
        negative_checks='data/development_regression_checks.json',independent_roles_available=False,new_api_calls=0),ensure_ascii=False,indent=2)+'\n')
    print('Public source pins PASS; independent gate/regression/test unavailable')

if __name__=='__main__':main()
