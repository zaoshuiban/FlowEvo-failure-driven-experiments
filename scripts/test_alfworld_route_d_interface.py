import copy,json,unittest
from alfworld_route_d_interface import public_state,parse_action,discover

class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.case=dict(goal='public goal', initial={'observation':'start'},
            steps=[dict(action='look',observation='seen',commands=['look']) for _ in range(16)],
            skills=['FORBIDDEN'],historical_won=False,task={'private':'FORBIDDEN'},future='FORBIDDEN')
    def test_public_boundary(self):
        p=public_state(self.case)
        self.assertNotIn('FORBIDDEN',json.dumps(p));self.assertEqual(len(p['history']),16)
        self.assertEqual(p['remaining_actions'],34)
    def test_invalid_does_not_execute_or_replace(self):
        class Env:
            def step(self,a):raise AssertionError('invalid action changed state')
        receipts={};states=[]
        def choose(state,n):
            states.append(copy.deepcopy(state))
            return {'choices':[{'finish_reason':'stop','message':{'content':'{"action":"illegal","reason":"x"}'}}]}
        result=discover(self.case,Env(),choose,lambda k,v:receipts.update({k:v}),None)
        self.assertEqual(result['environment_actions'],0);self.assertEqual(result['model_requests'],5)
        self.assertEqual(len({json.dumps(s['history']) for s in states}),1)
        self.assertEqual(len(receipts),10)
    def test_exact_legality_and_duplicates(self):
        for s in ['{"action":"look","action":"other","reason":"x"}', '{}{}', '{"action":" look","reason":"x"}']:
            self.assertEqual(parse_action(s,['look'])['status'],'DELIVERY_ERROR')
        self.assertEqual(parse_action('{"action":"look","reason":"x"}',['look'])['action'],'look')
    def test_original_remaining_budget(self):
        class Env:
            calls=0
            def step(self,a):self.calls+=1;return dict(action=a,observation='seen',commands=['look'],won=False,done=False)
        env=Env()
        result=discover(self.case,env,lambda s,n:{'choices':[{'finish_reason':'stop','message':{'content':'{"action":"look","reason":"x"}'}}]},lambda k,v:None,lambda a,r:r)
        self.assertEqual(env.calls,34);self.assertEqual(result['stop_reason'],'ACTION_LIMIT')
if __name__=='__main__':unittest.main()
