import pathlib,json,hashlib,csv
R=pathlib.Path(__file__).resolve().parents[2];P=R/'runs/s20_gmp_pilot12_20261026_01';O=pathlib.Path(__file__).parent
rows=[json.loads(x) for x in (P/'solve_budget.jsonl').read_text().splitlines()];req={};prev='0'*64
for r in rows:
 d={k:v for k,v in r.items() if k!='record_hash'};assert r['previous_hash']==prev;assert hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==r['record_hash'];prev=r['record_hash'];p=r['payload']
 if r['kind']=='RESERVED':req[p['request_id']]=dict(p,status='RESERVED')
 elif r['kind']=='SETTLED':req[p['request_id']].update(status='SETTLED',settlement=p)
 elif r['kind']=='UNKNOWN':req[p['request_id']]['status']='UNKNOWN'
model=[x for x in req.values() if x['kind']=='model'];responses={x['request_id']:x for x in json.loads((P/'solve_requests.json').read_text())};lines=[]
for x in model:
 q=responses[x['request_id']];lines.append(dict(request_id=x['request_id'],status=q['status'],reserved_usd=x['cost_upper_microusd']/1e6,settled_tokens=x.get('settlement',{}).get('tokens'),invoice_amount_present='cost_microusd' in x.get('settlement',{}),provider_id=q.get('raw_response',{}).get('id'),request_hash=x['request_hash']))
with (O/'request_cost_reconciliation.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(lines[0]));w.writeheader();w.writerows(lines)
success=sum(x['reserved_usd'] for x in lines if x['status']=='COMPLETED');unknown=sum(x['reserved_usd'] for x in lines if x['status']=='UNKNOWN');assert round(success+unknown,6)==.403943
out=dict(completed_reservations_usd=success,unknown_reservations_usd=unknown,completed_response_estimate_usd=.023944914,reservation_minus_response_estimate_usd=round(success-.023944914,9),money_settlement_present=sum(x['invoice_amount_present'] for x in lines),tool_reserved_usd=sum(x['cost_upper_microusd'] for x in req.values() if x['kind']=='tool')/1e6,unknown_recoverable=False,reason='No provider completion id, response or headers persisted; local request_id not sent as idempotency key. TLS handshake failure suggests pre-HTTP failure but no provider reconciliation proof. No resend.',old_run_unchanged=True)
(O/'reconciliation.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
