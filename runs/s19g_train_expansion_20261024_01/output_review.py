import pathlib,json,time
P=pathlib.Path(__file__).parent
# Human output-contract review only; no solver outcomes. Exact-token comparator cannot accept arbitrary witnesses/case variations.
nonunique={875,1818,1869,630,117,2279,2407,338,665,2682,2324,1659,1581,1265,95,457,1925}
caseflex={2624,1118,2597,2534,1640,1335}
ambiguous={63,492}
rows=json.loads((P/'candidate_order.json').read_text());out=[]
for x in rows:
 n=x['row'];reason='NONUNIQUE_WITNESS_REQUIRES_SPJ' if n in nonunique else 'CASE_FLEXIBLE_REQUIRES_DIFFERENT_COMPARATOR' if n in caseflex else 'CONSERVATIVE_OUTPUT_SCOPE' if n in ambiguous else None
 out.append({'id':x['id'],'output_contract':x['output_contract'],'accepted':reason is None,'reason':reason})
(P/'output_contract_review.json').write_text(json.dumps({'reviewed_at':time.time(),'basis':'all188 literal output contracts reviewed before reference execution; no target-model output; fixed exclusion ids and reasons; no official train SPJ index assumed','rows':out},ensure_ascii=False,indent=2));print('eligible after output review',sum(x['accepted'] for x in out))
