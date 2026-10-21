"""Descriptive paired task analysis; two tasks do not support general causal claims."""
import collections,itertools,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 ledger=json.loads((ROOT/'e2_results/ledger.json').read_text());grades=json.loads((ROOT/'e2_results/grades_all.json').read_text());planned=json.loads((ROOT/'e2_frozen/calls.json').read_text());lookup={g['call_id']:g for g in grades};tasks=sorted({c['task_id'] for c in planned});conditions={};matrix={t:{} for t in tasks}
 assert len(lookup)==len(grades)
 for condition in ['R0','R1','R2']:
  cs=[c for c in ledger['calls'] if c['condition']==condition];gs=[g for g in grades if g['condition']==condition];n=len(gs);success=sum(g['audited_hidden']['passed'] for g in gs);total=sum(c.get('usage',{}).get('total_tokens',0) for c in cs);unique=sum(any(g['audited_hidden']['passed'] for g in gs if g['task_id']==t) for t in tasks)
  conditions[condition]={'dispatched_calls':len(cs),'graded_calls':n,'audited_pass':success,'recovery_rate':success/n if n else None,'original_v2_pass':sum(g['original_v2_hidden']['passed'] is True for g in gs),'prompt_tokens':sum(c.get('usage',{}).get('prompt_tokens',0) for c in cs),'completion_tokens':sum(c.get('usage',{}).get('completion_tokens',0) for c in cs),'reasoning_tokens_included_in_completion':sum(c.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens',0) for c in cs),'total_tokens':total,'mean_latency_seconds':sum(c.get('latency_s',0) for c in cs)/len(cs) if cs else None,'tokens_per_successful_repair_call':total/success if success else None,'unique_tasks_recovered_at_least_once':unique,'tokens_per_task_recovered_at_least_once':total/unique if unique else None,'finish_reasons':dict(collections.Counter(c.get('finish_reason','UNRETURNED') for c in cs))}
  for t in tasks:
   rows=sorted((g for g in gs if g['task_id']==t),key=lambda x:x['repeat']);matrix[t][condition]={'runs':[{'repeat':g['repeat'],'status':g['audited_hidden']['status'],'old_v2_status':g['original_v2_hidden']['status'],'total_tokens':g['usage']['total_tokens']} for g in rows],'pass_rate':sum(g['audited_hidden']['passed'] for g in rows)/len(rows) if rows else None}
 contrasts={}
 if len(grades)==len(planned):
  for a,b in [('R1','R0'),('R2','R1'),('R2','R0')]:
   differences=[matrix[t][a]['pass_rate']-matrix[t][b]['pass_rate'] for t in tasks];bootstrap=sorted(sum(draw)/len(tasks) for draw in itertools.product(differences,repeat=len(tasks)));lo=bootstrap[max(0,math.ceil(.025*len(bootstrap))-1)];hi=bootstrap[math.ceil(.975*len(bootstrap))-1]
   contrasts[a+'-'+b]={'mean_task_paired_difference':sum(differences)/len(tasks),'task_differences':dict(zip(tasks,differences)),'exploratory_task_bootstrap_95_percentile':[lo,hi],'independent_tasks':len(tasks),'warning':'n=2, auxiliary truncation cohort; bootstrap is unstable and does not support general causal inference.'}
 assert sum(c.get('usage',{}).get('total_tokens',0) for c in ledger['calls'])==ledger['actual_reported_tokens']
 assert len(ledger['calls'])<=72 and ledger['charged_or_reserved_tokens']<=3000000
 models=collections.Counter(c.get('model','UNRETURNED') for c in ledger['calls']);summary={'status':ledger['status'],'planned_calls':len(planned),'dispatched_calls':len(ledger['calls']),'graded_calls':len(grades),'actual_total_tokens':ledger['actual_reported_tokens'],'conservative_charged_or_reserved_tokens':ledger['charged_or_reserved_tokens'],'actual_models':dict(models),'conditions':conditions,'per_task':matrix,'paired_contrasts':contrasts,'primary_algorithm_failure_cohort_tasks':0,'identical_feedback_negative_control_tasks':0,'auxiliary_implementation_completeness_tasks':len(tasks),'no_hidden_r2_counterexamples':True,'cost_currency':None,'cost_currency_reason':'No verified unit price; report all actual token usage without inventing currency cost.'}
 (ROOT/'e2_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
