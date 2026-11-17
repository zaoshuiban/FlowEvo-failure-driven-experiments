import tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import collect_alfworld_a4_checkpoints as C
class Tests(unittest.TestCase):
 def test_limits(self):
  self.assertEqual(C.LIMITS['environment_steps'],80*9*50);C.configure();self.assertEqual(C.D.previous.LIMITS['resets'],720)
 def test_pending_game_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);C.D.EvidenceStore(out/'collection.jsonl').append('GAME_STARTED',{'id':'x'},time.time())
   with patch.object(C,'verify',return_value=({},{})),self.assertRaises(C.RunUnhealthy):C.probe(out)
 def test_all_games_no_candidate_path(self):
  class Env:
   def __init__(self,*a,**k):pass
   def initialize(self,**k):pass
   def close(self):pass
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);rows=[{'task':{'task_id':str(i),'split':'train'},'role':'INDEPENDENT_TEST','stratum':'strict_scene'} for i in range(80)]
   with patch.object(C,'verify',return_value=({'data_root':'dummy'},{'tasks':rows})),patch.object(C,'CollectionEnv',Env),patch.object(C,'verify_game',return_value='dummy'),patch.object(C.D.previous,'start',return_value=(SimpleNamespace(history=[]),'unsupported',{})),patch.object(C.D.previous,'find_subject',return_value=(None,'PUBLIC_GOAL_UNSUPPORTED')):
    a=C.probe(out);self.assertEqual(a['games'],80);self.assertEqual(a['paid_requests'],0);self.assertEqual(a['candidate_executions'],0)
    with patch.object(C,'CollectionEnv',side_effect=AssertionError('must not reset')):
     self.assertEqual(C.probe(out),a)
   self.assertEqual(len(list((out/'games').glob('*.json'))),80)
if __name__=='__main__':unittest.main()
