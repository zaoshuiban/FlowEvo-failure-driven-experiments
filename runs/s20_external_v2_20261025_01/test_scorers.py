"""Adversarial comparison fixtures, including documented departures from legacy scorers."""
import json,pathlib,hashlib
from scorer import accepts
P=pathlib.Path(__file__).parent
cases=[('apps','1 2','1 2',True),('apps','1 2','2 1',False),('apps','1 1 2','1 2',False),('apps','9007199254740993','9007199254740992',False),('apps','YES','yes',False),('apps','1\n2','1 2',True),('apps','1','',False),('apps','1','1 2',False),('lcb','1\n2','1 2',False),('lcb','1 2','1.0 2.00',True),('lcb','9007199254740993','9007199254740992',False),('lcb','a b','b a',False),('lcb','1','1.000001',False),('lcb',' a \n b ','a\nb',True),('cc','abc def 123','abc def 123',True),('cc','abc def 123','abc def 124',False),('cc','abc def 123','abc def 123 x',False),('cc','abc def 123','ABC DEF 123',True),('cc','123','123.000001',False),('cc','123','123.1',False),('cc','1.0','1.000001',True),('cc','9007199254740993','9007199254740992',False),('cc','1','nan',False),('cc','1','inf',False),('cc','Á','á',False),('cc','10','1_0',False),('cc','1','١',False)]
rows=[]
for ds,expected,actual,want in cases:
 got=accepts(ds,expected,actual);assert got==want,(ds,expected,actual,got,want)
 rows.append(dict(dataset=ds,expected=expected,actual=actual,want=want,got=got))
(P/'scorer_unit_results.json').write_text(json.dumps(dict(passed=len(rows),rows=rows,model_requests=0,official_parity='LCB comparison source port; CC intentional exact-integer correction; APPS ordered-token research scorer, not legacy leaderboard parity'),indent=2))
print('PASS',len(rows))
