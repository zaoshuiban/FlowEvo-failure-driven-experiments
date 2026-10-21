import json,pathlib,unittest,sys
from comparison import stdio_equal,structured_equal,normalize_legacy,solver_feedback
from semantic import accepts,parse,InvalidTest
from contracts import validate,expected_value
from preflight import preflight

class ComparisonTests(unittest.TestCase):
 def test_integer_precision(self):
  self.assertFalse(stdio_equal(str(10**25+1),str(10**25),{}));self.assertTrue(stdio_equal('1 2\n','1  2 \n',{}));self.assertFalse(stdio_equal('1 2','2 1',{}))
 def test_float_boundaries(self):
  p={'epsilon':'1e-6','error_mode':'absolute'}
  self.assertTrue(stdio_equal('0.0625000000','0.0625',p));self.assertTrue(stdio_equal('1.000001','1',p));self.assertFalse(stdio_equal('1.000002','1',p))
  for x in ['nan','NaN','inf','-inf']:self.assertFalse(stdio_equal(x,'1',p))
 def test_typed_returns(self):
  self.assertFalse(structured_equal(True,1,{}));self.assertFalse(structured_equal(1,[1],{}));self.assertFalse(structured_equal([1,2],[2,1],{}));self.assertFalse(structured_equal(1.0,1,{}))
  self.assertTrue(structured_equal([1,True],[1,True],{}))
 def test_codes(self):
  self.assertEqual(normalize_legacy('lcb',-2),'WRONG_ANSWER');self.assertEqual(normalize_legacy('lcb',-3),'TIME_LIMIT');self.assertEqual(normalize_legacy('taco',-2),'LOAD_ERROR')
  self.assertEqual(normalize_legacy('lcb',-4,{'error':'SyntaxError: invalid syntax'}),'COMPILE_ERROR')
 def test_no_gold_feedback(self):
  v=solver_feedback({'status':'WRONG_ANSWER','expected':'secret','input':'hidden','traceback':'private'})
  self.assertNotIn('secret',json.dumps(v));self.assertNotIn('hidden',json.dumps(v));self.assertEqual(set(v),{'status','feedback'})

# Independent small witnesses, including different valid constructions and deliberately invalid output.
CASES=[
 ('taco_0594','1\n3\n',['1 2 3','3 2 1'],['1 1 2','1 2']),
 ('taco_0137','2 2\n1 2',['YES\n1\n1 2','YES\n2\n2 1'],['NO','YES 1 2 2']),
 ('taco_0510','5',['5 12 13','13 12 5'],['3 4 5','5 11 13']),
 ('taco_0831','4',['0\n2 1 4','0\n2 2 3'],['0 2 1 2','1 2 1 4']),
 ('taco_0946','2 5',['2 3 4','2 5 4'],['-1','2 3 5']), # second positive replaced below
 ('taco_0720','2\na b\nc d',['2 a b c d','2 c d a b'],['2 a d c b','1 a b']),
 ('taco_0552','3 4\n2 2 3',['2 1 2','2 2 1'],['1 3','2 1 3']),
 ('taco_0056','1\n3',['0 2 3','2 0 1'],['0 1 2','-1']),
 ('taco_0617','6\n1 2 3 1 2 3',['2 1 2 3 4 5 6','2 4 2 6 1 5 3'],['1 1 2 3','2 1 2 3 1 5 6']),
 ('taco_0054','5858 1234',['1624','4623'],['4624','0624']),
 ('taco_0444','2\n3 75\n100 100',['2 5\n3 1','1 25\n1 1'],['0 0\n1 1','2 5\n0 0']),
 ('taco_0519','1\n2 1\n1 4',['2','3'],['1','4']),
 ('taco_0638','1\n2 2',['0\n10\n01','0\n01\n10'],['0\n11\n00','2\n10\n01']),
 ('taco_0574','1 2',['3 4','4 3'],['1 1','0 1']),
 ('taco_0347','1\n24',['3\n4','8\n3'],['-1\n-1','2\n4']),
 ('taco_0422','1\n3',['1 -1 1','-1 1 -1'],['0 0 0','1 1 1']),
 ('taco_0771','1\n3',['2 1 3','2 3 1'],['1 2 3','1 1 2']),
 ('taco_0381','1\n4 7\n0 1 2 3',['4','7'],['0','8']),
 ('taco_0945','1\n2\n1 1 1 2 2\n2 2 2 1 1',['1','1\n'],['2','-1']),
 ('lcb_atcoder_abc350_c','3\n2 1 3',['1\n1 2','3\n1 2\n1 1\n2 2'],['0','1 1 3']),
 ('lcb_atcoder_abc311_c','4\n2 1 4 3',['2 1 2','2 3 4'],['3 1 2 3','2 1 1']),
 ('lcb_atcoder_abc315_e','4\n2 2 3\n1 4\n0\n0',['4 2 3','3 4 2'],['2 4 3','4 2']),
 ('lcb_atcoder_abc366_g','3 3\n1 2\n1 3\n2 3',['Yes 1 1 1','Yes 4 4 4'],['No','Yes 1 2 3']),
 ('lcb_atcoder_arc181_c','3\n1 2 3\n2 1 3',['001\n101\n110','001\n101\n111'],['000\n000\n000','001\n101\n100']),
]
CASES[4]=('taco_0946','2 6',['2 3 4','4 5 6'],['-1','2 3 5'])
# Gray path must stay within 0..n-1.
CASES[7]=('taco_0056','1\n3',['1 0 2','2 0 1'],['0 1 2','-1'])
# Lower median must change at each prefix; 2,3,1 has equal first two medians.
CASES[16]=('taco_0771','1\n3',['2 1 3','3 1 2'],['1 2 3','2 3 1'])

class SemanticTests(unittest.TestCase):
 def test_witnesses(self):
  for tid,inp,good,bad in CASES:
   with self.subTest(task=tid):
    d=parse(tid,inp)
    for out in good:self.assertTrue(accepts(tid,d,out),(tid,'good',out))
    for out in bad:self.assertFalse(accepts(tid,d,out),(tid,'bad',out))
 def test_magic_square(self):
  good=[[16,2,3,13],[5,11,10,8],[9,7,6,12],[4,14,15,1]];d=parse('taco_0796',[4]);self.assertTrue(accepts('taco_0796',d,good));self.assertTrue(accepts('taco_0796',d,list(reversed(good))));bad=[row[:] for row in good];bad[0][0]=1;self.assertFalse(accepts('taco_0796',d,bad))
 def test_no_solution_certificate(self):
  d=parse('lcb_atcoder_abc366_g','2 1\n1 2');self.assertTrue(accepts('lcb_atcoder_abc366_g',d,'No'));self.assertFalse(accepts('lcb_atcoder_abc366_g',d,'Yes 1 1'))
 def test_input_contract(self):
  with self.assertRaises(InvalidTest):parse('lcb_atcoder_abc350_c','3\n2 2 3')
  with self.assertRaises(InvalidTest):parse('taco_0594','1\n1')

class DataTests(unittest.TestCase):
 def task(self,tid,fn=None,ds='taco'):return {'task_id':tid,'dataset':ds,'function_name':fn,'starter_code':''}
 def test_invalid_source_witnesses(self):
  with self.assertRaises(InvalidTest):validate(self.task('taco_0038'),'8 6\n8 1\n8 2\n8 3\n8 4\n8 5\n8 6')
  with self.assertRaises(InvalidTest):validate(self.task('taco_0715'),'1\n8 7\n2 3 4 5 6 7 8 9')
  with self.assertRaises(InvalidTest):validate(self.task('lcb_leetcode_3344','minimumDistance','lcb'),'[0,0]')
  with self.assertRaises(InvalidTest):validate(self.task('taco_0947','split_odd_and_even'),[999900])
 def test_return_envelope(self):
  task=self.task('taco_0191','vector_length');self.assertEqual(expected_value(task,[1]),1)
  with self.assertRaises(InvalidTest):expected_value(task,[1,2])
 def test_no_vacuous_pass(self):
  t=self.task('taco_0947','split_odd_and_even');t['input_output']=json.dumps({'inputs':[[100]],'outputs':[[[1]]]})
  pre,cases=preflight(t,{'protocol':'function','comparison':'structured'})
  self.assertEqual(pre['status'],'NO_VALID_TESTS');self.assertEqual(cases,[])

if __name__=='__main__':unittest.main(verbosity=2)
