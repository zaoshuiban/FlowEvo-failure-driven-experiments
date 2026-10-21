import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from failure_evo import Budget,BoundedCompiler,LearningPipeline
from failure_evo.failure_events import public_check_outcome

class PipelineAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.requests=[];self.checks=[]
        def provider(q):
            self.requests.append(q)
            return {'model':'fixture','specification':'public specification','code':'def repair_operator(p):\n return {"status":"declined"}\n','usage':{'total_tokens':1}}
        self.compiler=BoundedCompiler(provider,Budget(max_calls=14,clock=lambda:0),self.root/'compiler','fixture')
        def checker(code,data,timeout):
            self.checks.append(data['shard_id']);return {'eligible':True,'score':1}
        self.pipeline=LearningPipeline(self.root/'pipeline',self.compiler,Budget(clock=lambda:0),checker,checker)
        self.job={'job_id':'job','stream_id':'s','family_id':'artifact','evidence_ids':['fact'],
                  'public_evidence':[{'provenance_group_id':'source'}]}
        self.data={role:{'shard_id':role,'source_groups':[role]} for role in ['design','gate','regression']}
    def tearDown(self):self.tmp.cleanup()
    def test_complete_and_resume_without_calls(self):
        result=self.pipeline.run(self.job,at=1,revise=True,**self.data)
        self.assertEqual(result['status'],'ready_for_experimental_review');self.assertEqual(len(self.requests),7)
        self.assertEqual(len(self.checks),8)
        self.assertEqual(self.pipeline.run(self.job,at=1,revise=True,**self.data),result)
        self.assertEqual(len(self.requests),7);self.assertEqual(len(self.checks),8)
        self.assertTrue(all('gate' not in str(q) and 'regression' not in str(q) for q in self.requests))
    def test_failure_not_retried(self):
        def fail(*args):raise ConnectionError('fixture')
        self.pipeline.gate_checker=fail
        with self.assertRaises(ConnectionError):self.pipeline.run(self.job,at=1,**self.data)
        count=len(self.requests)
        with self.assertRaises(RuntimeError):self.pipeline.run(self.job,at=1,**self.data)
        self.assertEqual(len(self.requests),count)
    def test_protocol_change_rejected(self):
        self.pipeline.run(self.job,at=1,**self.data)
        with self.assertRaises(ValueError):self.pipeline.run(self.job,at=1,revise=True,**self.data)
    def test_source_overlap_rejected_before_generation(self):
        self.data['gate']['source_groups']=['source']
        with self.assertRaises(ValueError):self.pipeline.run(self.job,at=1,**self.data)
        self.assertEqual(self.requests,[])
    def test_failed_gate_keeps_shadow(self):
        self.pipeline.gate_checker=lambda *a:{'eligible':False,'score':0}
        out=self.pipeline.run(self.job,at=1,**self.data)
        self.assertEqual(out['status'],'shadow_retained')
        self.assertEqual(len(self.requests),4)
    def test_three_public_outcomes(self):
        self.assertEqual(public_check_outcome({'visibility':'public','status':'PUBLIC_PASS','tests_run':1,'tests_passed':1})['public_check_outcome'],'passed')
        self.assertEqual(public_check_outcome({'visibility':'public','status':'WRONG_ANSWER','tests_run':1})['public_check_outcome'],'failed')
        for raw in [{'visibility':'public','status':'PUBLIC_PASS','tests_run':0,'tests_passed':0},{'visibility':'private','status':'WRONG_ANSWER','tests_run':1}]:
            self.assertEqual(public_check_outcome(raw)['public_check_outcome'],'unavailable')

if __name__=='__main__':unittest.main()
