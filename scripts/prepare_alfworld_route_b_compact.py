"""Freeze local B0.1 artifacts only. No API, environment, or authorizations."""
import argparse
from pathlib import Path
from alfworld_.route_b_information import load_cohort
from alfworld_.route_b_compact_projection import prepare,validate,decode
from failure_evo.math_stream import sha
from failure_evo.contracts import canonical,fingerprint
from run_alfworld_a4_confirmatory import commit

def freeze(out,source):
    if out.exists():raise FileExistsError('new run directory required')
    cohort=load_cohort(source);result=validate(prepare(cohort),cohort)
    out.mkdir(parents=True,mode=0o700)
    commit(out/'projection.private.json',result)
    commit(out/'source_binding.private.json',cohort['files'])
    for arm,w in result['wires'].items():commit(out/f'{arm}_wire.private.json',w)
    sources=[Path(__file__).resolve(),Path(__import__('alfworld_.route_b_information',fromlist=['x']).__file__).resolve(),
        Path(__import__('alfworld_.route_b_compact_projection',fromlist=['x']).__file__).resolve()]
    summary=dict(version=result['version'],selection=result['selection'],strata=result['strata'],
        measurements=result['measurements'],byte_limit_passed=result['byte_limit_passed'],
        full_quota_coverage=result['full_quota_coverage'],paid_requests=0,new_environment_steps=0,
        source_sha256={str(p):sha(p) for p in sources},packet_sha256=fingerprint(result),
        original_sources_unchanged=all(sha(p)==h for p,h in cohort['files'].items()),
        lossless_roundtrip=True,common_target_catalog=120,
        status='EXPLORATORY_INPUT_READY' if result['byte_limit_passed'] else 'INPUT_SIZE_BLOCKED',
        limits=result['limits'],paid_authorization=False,tokenizer_measured=False,
        remaining=['lamp has only one clean same-cohort success; no stable lamp generalization claim',
            'actual provider context/token validation and generation/revision budgets require separate preflight',
            'new paid authorization required'])
    return commit(out/'summary.json',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path,default=Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01')
    a=p.parse_args();print(canonical(freeze(a.output.resolve(),a.source.resolve())))
