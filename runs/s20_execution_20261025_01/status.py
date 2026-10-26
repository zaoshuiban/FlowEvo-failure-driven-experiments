import pathlib,json,collections
P=pathlib.Path(__file__).parent;R=P.parents[1]
for arm in 'GMF':
 p=R/'runs'/f's20_taco80_{arm.lower()}_20261025_01'
 rows=[json.loads(x.read_text()) for x in p.glob('branches/*/*/workflow.json')];req=[json.loads(x.read_text()) for x in p.glob('wire/*/*/response.json')]
 print(arm,'tasks',len(rows),'public_pass',sum(x['status']=='PUBLIC_ACCEPTED' for x in rows),'responses',len(req),'tokens',sum(x.get('usage',{}).get('total_tokens',0) for x in req),'learning_responses',len(list(p.glob('wire/learning/*/response.json'))),'hooks',sum(len(x.get('hook_events',[])) for x in rows),flush=True)
print((P/'execution_status.json').read_text()[:160],flush=True)
