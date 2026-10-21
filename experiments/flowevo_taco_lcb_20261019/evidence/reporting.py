import datetime,html,json,pathlib

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def build_report(root,levels,config,stopped):
 groups=[];totals={};models=set();usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'reasoning_tokens':0,'api_calls':0}
 for ds,difficulties in levels.items():
  path=root/'data'/f'{ds}_manifest.json';manifest=read(path) if path.exists() else None
  total={'dataset':ds,'selected':0,'completed':0,'first_pass':0,'final_pass':0,'available':sum(manifest['available'].values()) if manifest else None}
  for diff in difficulties:
   folder=root/'runs'/f'{ds}_{diff}';rows=[read(p) for p in folder.glob('*/result.json')]
   g={'dataset':ds,'difficulty':diff,'available':manifest['available'][diff] if manifest else None,'selected':manifest['selected'][diff] if manifest else None,'completed':len(rows),'first_pass':sum(r['first_pass'] for r in rows),'final_pass':sum(r['passed'] for r in rows)}
   for label in ['first','final']:g[label+'_rate']=g[label+'_pass']/g['selected'] if g['selected'] and g['completed']==g['selected'] else None
   g['observed_final_rate']=g['final_pass']/g['completed'] if g['completed'] else None
   groups.append(g)
   for k in ['selected','completed','first_pass','final_pass']:total[k]+=g[k] or 0
   for p in folder.glob('*/*.response.json'):
    response=read(p);models.add(response.get('model','unknown'));u=response.get('usage',{});usage['api_calls']+=1
    for k in ['prompt_tokens','completion_tokens','total_tokens']:usage[k]+=u.get(k,0)
    usage['reasoning_tokens']+=u.get('completion_tokens_details',{}).get('reasoning_tokens',0)
  for label in ['first','final']:total[label+'_rate']=total[label+'_pass']/total['selected'] if manifest and total['selected'] and total['completed']==total['selected'] else None
  totals[ds]=total
 complete=all(g['selected'] is not None and g['completed']==g['selected'] for g in groups)
 summary={'status':'complete' if complete else ('stopped' if stopped else 'running'),'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':config,'returned_models':sorted(models),'usage':usage,'datasets':totals,'difficulty_groups':groups}
 write(root/'reports/summary.json',summary)
 def pct(v):return 'Pending' if v is None else f'{100*v:.2f}%'
 rows=''.join(f"<tr><td>{g['dataset']}</td><td>{g['difficulty']}</td><td>{g['available']}</td><td>{g['selected']}</td><td>{g['completed']}</td><td>{g['first_pass']}</td><td>{pct(g['first_rate'])}</td><td>{g['final_pass']}</td><td>{pct(g['final_rate'])}</td></tr>" for g in groups)
 totals_html=''.join(f"<p><b>{ds.upper()}</b>: completed {v['completed']}/{v['selected']}; solved {v['final_pass']}; success rate {pct(v['final_rate'])}.</p>" for ds,v in totals.items())
 page='<!doctype html><meta charset="utf-8"><title>FlowEvo + DeepSeek results</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#17202a}table{border-collapse:collapse;width:100%;margin:24px 0}td,th{border-bottom:1px solid #ddd;padding:10px;text-align:left}th{background:#edf3fa}small{color:#555}</style>'
 page+=f"<h1>FlowEvo + DeepSeek benchmark</h1><p>Status: <b>{summary['status']}</b> | Updated {summary['updated_utc']}</p>"+totals_html
 page+='<table><tr><th>Dataset</th><th>Difficulty</th><th>Available</th><th>Sampled</th><th>Finished</th><th>First-pass</th><th>First rate</th><th>Final passed</th><th>Final rate</th></tr>'+rows+'</table>'
 page+='<p>Requested model: deepseek-reasoner. Returned model(s): '+html.escape(', '.join(sorted(models)) or 'pending')+'. Thinking mode enabled; max 32,768 tokens per request.</p>'
 page+='<p>Success requires passing every official test case. FlowEvo uses at most five candidates: initial generation, two independent alternatives, and two repairs using failure-category feedback and an existing skill when available. Stop at the first accepted candidate.</p>'
 page+='<p>The adaptive final rate uses verifier feedback, including hidden-test pass/fail. It must not be compared directly to hidden-test-blind pass@1. The first-candidate success rate is reported separately. No private input/output or reference solution is sent to the model.</p>'
 page+='<p>Each dataset/difficulty has an independent initially empty online skill library. Selection and episode order use SHA256(seed|dataset|difficulty|source_id), seed 20261019; take the first min(100, available) per group. TACO uses its official test split; LiveCodeBench uses release_v6, all six release files.</p>'
 page+='<p>This adapter uses the official code_math/runner.py ours condition and CodeSkillLibrary. It is the released code/math implementation, not a reimplementation of the other environments in the paper. Configuration records all adapter changes. Pending rates are left blank until the full selected group finishes; API/infrastructure errors stop the experiment rather than count as solving failures.</p>'
 page+=f"<p>API calls: {usage['api_calls']}; total tokens: {usage['total_tokens']:,}; completion tokens: {usage['completion_tokens']:,}.</p><small>FlowEvo commit: {config['flowevo_commit']}</small>"
 tmp=root/'reports/report.html.tmp';tmp.write_text(page,encoding='utf-8');tmp.replace(root/'reports/report.html')
 return summary
