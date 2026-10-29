"""Run only engineering fixtures, retaining real Linux Worker evidence. No paid API."""
import argparse,datetime,importlib.util,json,os,pathlib,sys,unittest,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
out=pathlib.Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
os.environ['MATH_P0_ARTIFACT_DIR']=str(out/'fixtures')
# Fail closed even if an accidental direct HTTP call is introduced in a test.
def no_http(*args,**kwargs):raise RuntimeError('P0_PAID_API_DISABLED')
urllib.request.urlopen=no_http
import requests
requests.sessions.Session.request=no_http
spec=importlib.util.spec_from_file_location('math_acceptance',ROOT/'scripts/tests/test_math_no_gold.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
with (out/'tests.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
summary=dict(engineering_only=True,real_model_requests=0,real_worker=True,tests=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors),failures=[(str(t),e) for t,e in result.failures],errors=[(str(t),e) for t,e in result.errors],recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False));sys.exit(not result.wasSuccessful())
