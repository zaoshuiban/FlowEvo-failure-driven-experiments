import contextlib,io,json,pathlib,tempfile,unittest
from unittest.mock import patch
import run_e2
class FakeResponse:
 status_code=200
 def json(self):return {'model':'m','id':'fake','usage':{'prompt_tokens':40,'completion_tokens':60,'total_tokens':100},'choices':[{'finish_reason':'stop','message':{'content':'pass'}}]}
class FakeSession:
 trust_env=True
 count=0
 def post(self,*a,**k):self.count+=1;return FakeResponse()
class Safety(unittest.TestCase):
 def run_fixture(self,max_calls=72,max_tokens=3000000,model='m',http=200):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp);root=base/'study';frozen=root/'e2_frozen';frozen.mkdir(parents=True);(base/'.deepseek-key').write_text('dummy-test-only')
   manifest={'hashes':{},'max_calls':max_calls,'max_total_tokens':max_tokens};(frozen/'manifest.json').write_text(json.dumps(manifest));calls=[{'call_id':str(i),'task_id':'test','condition':'R0','repeat':i,'expected_actual_model':model,'request':{'max_tokens':32768,'messages':[]}} for i in [1,2]];(frozen/'calls.json').write_text(json.dumps(calls))
   session=FakeSession()
   if http!=200:
    response=FakeResponse();response.status_code=http
    session.post=lambda *a,**k:response
   with patch.object(run_e2,'ROOT',root),patch.object(run_e2,'BASE',base),patch.object(run_e2.requests,'Session',return_value=session),contextlib.redirect_stdout(io.StringIO()):run_e2.main()
   return json.loads((root/'e2_results/ledger.json').read_text())
 def test_budget_stops_before_dispatch(self):
  d=self.run_fixture(max_tokens=100);self.assertEqual(d['status'],'BUDGET_STOP');self.assertEqual(d['calls'],[])
 def test_call_ceiling(self):
  d=self.run_fixture(max_calls=1);self.assertEqual(len(d['calls']),1);self.assertEqual(d['actual_reported_tokens'],100);self.assertEqual(d['status'],'BUDGET_STOP')
 def test_model_mismatch_stops(self):
  d=self.run_fixture(model='different');self.assertEqual(len(d['calls']),1);self.assertEqual(d['status'],'MODEL_MISMATCH_STOP')
 def test_http_failure_has_no_retry(self):
  d=self.run_fixture(http=429);self.assertEqual(len(d['calls']),1);self.assertEqual(d['status'],'API_STOP');self.assertGreater(d['charged_or_reserved_tokens'],32768)
 def test_success_accounting(self):
  d=self.run_fixture();self.assertEqual(d['status'],'COMPLETED');self.assertEqual(d['actual_reported_tokens'],200);self.assertEqual(d['charged_or_reserved_tokens'],200)
if __name__=='__main__':unittest.main()
