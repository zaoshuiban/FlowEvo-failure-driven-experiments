import tempfile,time,unittest
from pathlib import Path
from alfworld_absolute_deadline import Capture,absolute_deadline
class DeadlineTests(unittest.TestCase):
 def test_continuous_bytes_do_not_reset_absolute_deadline(self):
  class Response:
   status=200
   def read1(self,n):time.sleep(.01);return b' '
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'partial';start=time.monotonic()
   with self.assertRaises(TimeoutError):
    with absolute_deadline(.12):Capture(Response(),p).read(10000)
   self.assertLess(time.monotonic()-start,.5);self.assertGreater(p.stat().st_size,0)
 def test_complete_response_unchanged(self):
  class Response:
   status=200
   def __init__(self):self.parts=iter([b'{"a":',b'1}',b''])
   def read1(self,n):return next(self.parts)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'partial'
   with absolute_deadline(1):raw=Capture(Response(),p).read(100)
   self.assertEqual(raw,b'{"a":1}');self.assertEqual(p.read_bytes(),raw)
if __name__=='__main__':unittest.main()
