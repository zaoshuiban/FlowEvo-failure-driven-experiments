import itertools,unittest
from semantic import parse,accepts
CASES=[
 ('taco_0649','1\n2 2\nab\nbb',['ab','bb'],['cc','-1']),
 ('taco_0485','3\n1 2\n2 3\n1 2 1',['YES 2','YES\n2'],['NO','YES 1']),
 ('taco_0577','1\n4 6 13',['4 6 5','5 4 6'],['4 4 4','3 4 4']),
 ('taco_0205','3\n2 1 3',['2 2 1 2 1 3','2 1 3 2 2 1'],['3 1 1 1 2 1 3','1 3 1 2 3']),
 ('taco_0220','2\n13 24 13 45',['4 1 2 2 1','4 2 1 1 2'],['2 1 1 2 2','4 1 1 1 2']),
 ('taco_0308','3 1 1\n1 2\n1 3',['1 2 3','1 3 2'],['0','1 1 2']),
 ('taco_0984','01',['1 1\n1 2','1 4\n3 1'],['4 1 1 1','1 1 1 1']),
 ('taco_0639','4 20 32\n21 11 11 12',['Yes 1 3 1 2 3 4','Yes 1 3 1 4 3 2'],['No','Yes 2 2 1 2 3 4']),
]
class Extra(unittest.TestCase):
 def test_witnesses(self):
  for tid,inp,good,bad in CASES:
   with self.subTest(task=tid):
    data=parse(tid,inp)
    for out in good:self.assertTrue(accepts(tid,data,out),(tid,'valid',out))
    for out in bad:self.assertFalse(accepts(tid,data,out),(tid,'invalid',out))
 def test_server_infeasibility_exhaustive(self):
  for caps in itertools.product(range(1,4),repeat=4):
   for x in range(1,8):
    for y in range(1,8):
     feasible=False
     for group in itertools.product(range(3),repeat=4):
      a=[v for v,g in zip(caps,group) if g==1];b=[v for v,g in zip(caps,group) if g==2]
      if a and b and min(a)*len(a)>=x and min(b)*len(b)>=y:feasible=True;break
     self.assertEqual(accepts('taco_0639',(4,x,y,list(caps)),'No'),not feasible,(caps,x,y))
 def test_cube_optimum_exhaustive(self):
  for vals in itertools.product([10,11,12],repeat=6):
   best=max(len({vals[i] for i in ids})*len({vals[i] for i in range(6) if i not in ids}) for ids in itertools.combinations(range(6),3))
   import collections
   c=collections.Counter(vals);total=len(c)+sum(n>=2 for n in c.values());self.assertEqual(best,total//2*((total+1)//2))
if __name__=='__main__':unittest.main(verbosity=2)
