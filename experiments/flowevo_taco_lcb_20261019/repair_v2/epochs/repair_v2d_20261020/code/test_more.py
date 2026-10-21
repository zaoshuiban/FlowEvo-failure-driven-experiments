import itertools,unittest
from semantic import parse,accepts
CASES=[
 ('taco_0173','1\nabacabaaacaac',['abacaba bac','abacaba\nbac'],['abacaba abc','-1']),
 ('taco_0295','5 3\n1 2\n2 3\n4 5\n2 1 2 2 1',['2 5 1 3 4','5 2 4 3 1'],['1 2 3 4 5','-1']),
 ('taco_0221','3\n2 0\n0 2\n2 0',['YES 1 2 1','YES 4 10 7'],['NO','YES 2 2 2']),
 ('taco_0083','2 1\n1 2 0',['1 1','1 2'],['0','Impossible']),
 ('taco_0119','2 2',['3 0 2 1 1 2 0','3 0 1 1 2 2 0'],['2 0 1 1 0','3 0 0 1 1 2 2']),
 ('taco_0408','2 2 0\n2 1\n1 2',['1 1 2','1\n1 2'],['0','1 2 1']),
 ('taco_0621','1\n9',['3 1 0 2','3 1 1 0'],['2 1 2','3 1 1 1']),
 ('taco_0343','2\n2 1 2\n2 1 2\n1\n2 2',['1 2','2 1'],['2 2','1 1']),
 ('taco_0238','3 5 1\n*****\n*.*.*\n*****',['1 ***** ***.* *****','1 ***** *.*** *****'],['0 ***** *.*.* *****','2 ***** ***** *****']),
 ('taco_0477','4\n4 3 2 1',['YES 4 1 4 2 1 3','YES 2 3 2 1 3 4'],['NO','YES 1 2 1 3 1 4']),
]
class More(unittest.TestCase):
 def test_witnesses(self):
  for tid,inp,good,bad in CASES:
   with self.subTest(task=tid):
    d=parse(tid,inp)
    for out in good:self.assertTrue(accepts(tid,d,out),(tid,'valid',out))
    for out in bad:self.assertFalse(accepts(tid,d,out),(tid,'invalid',out))
 def test_negative_certificates(self):
  for tid,inp,out in [('taco_0173','1\nhaaha','-1'),('taco_0295','2 1\n1 2\n1 1','-1'),('taco_0221','2\n0 0\n1 1','NO'),('taco_0083','3 3\n1 2 0\n2 3 0\n3 1 0','Impossible'),('taco_0477','3\n3 1 2','NO')]:self.assertTrue(accepts(tid,parse(tid,inp),out),tid)
if __name__=='__main__':unittest.main(verbosity=2)
