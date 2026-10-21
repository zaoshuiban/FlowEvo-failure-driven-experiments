"""Zero-API local acceptance; never imports or executes archived model clients."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(ROOT/'scripts/smoke_failure_evo_v2.py'), '--output-dir', str(out/'smoke')]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out/'acceptance.log').write_text(result.stdout + result.stderr)
    paths = list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    paths += [ROOT/p for p in (
        'experiments/flowevo_taco_lcb_20261019/evidence/benchmark.py',
        'FlowEvo/src/code_math/runner.py',
        'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/sandbox.py',
        'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py')]
    manifest = dict(platform=platform.system(), machine=platform.machine(), python=sys.version,
        source_location=str(ROOT), source_scope='downloaded local repository; no remote attestation requested',
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        new_api_calls=0, model_configuration='NOT_CONFIGURED_FOR_LIVE_CALLS',
        local_smoke='PASS' if result.returncode==0 else 'FAIL',
        linux_worker=dict(status='NOT_VALIDATED', operating_system=platform.system(),
            bwrap_available=bool(shutil.which('bwrap')), docker_available=bool(shutil.which('docker')),
            reason='Source hashing and unit fixtures do not certify real isolation'),
        paid_experiment_allowed=False)
    (out/'local_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ('platform','local_smoke','new_api_calls','linux_worker','paid_experiment_allowed')},indent=2))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
