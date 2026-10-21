# -*- coding: utf-8 -*-
"""E3-S0: deterministic, offline historical event and memory replay. No API calls."""
import ast, collections, csv, datetime, hashlib, json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT.parent
RAW=ROOT/'raw/runs'
SOURCE=ROOT/'raw/e3_s0_20261020/source'
STAGES=['l1','l2a','l2b','l3','l4']
def load(p): return json.loads(p.read_text())
def save(name,x):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def utc(ns): return datetime.datetime.fromtimestamp(ns/1e9,datetime.timezone.utc).isoformat()
def jsonl(name,rows): (ROOT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
def table(name,rows):
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    metadata=load(SOURCE/'file_metadata.json')
    parse310={(x['task_id'],x['stage']):x for x in load(SOURCE/'python310_static_parse.json')['results']}
    catalog={x['task_id']:x for x in load(BASE/'repair_v2/catalog.json')}
    inventory={(x['task_id'],x['stage']):x for x in load(BASE/'trusted_rgf_20261020/inventory_2132.json')}
    repaired={(x['task_id'],x['stage']):x for x in load(BASE/'repair_v2/epochs/repaired_reports_20261020/candidate_results.json')}
    e1={x['task_id']:x for x in load(BASE/'e1_e2_20261020/e1_cards_final.json')}
    audits={x['task_id']:x for x in load(BASE/'逐题机制审计.json')}
    trusted=BASE/'trusted_rgf_20261020'
    trusted_verdicts={(p.parent.name,p.stem):load(p) for p in (trusted/'verdicts').glob('*/*.json')}
    verified={(x['task_id'],x['original_stage']):x for x in load(trusted/'failure_mechanism_bank.json')}
    manifests=[load(SOURCE/(ds+'_manifest.json')) for ds in ['taco','lcb']]
    tasks=[x for m in manifests for x in m['tasks']]
    assert len(tasks)==len(catalog)==800 and len(inventory)==len(repaired)==2132
    issues=[]; checks=collections.Counter(); events=[]; stream_rows=[]; memory_rows=[]; edges=[]
    def check(ok,kind,**kw):
        checks[kind+'_checked']+=1
        if not ok: issues.append({'kind':kind,**kw})
    group_tasks=collections.defaultdict(list)
    for task in tasks: group_tasks[task['dataset']+'_'+task['difficulty']].append(task)
    for group,metas in sorted(group_tasks.items()):
        metas.sort(key=lambda t:t['order']); check([x['order'] for x in metas]==list(range(100)),'manifest_order',group=group)
        library=[]; previous_result_ns=None; pos=0
        for task in metas:
            tid=task['task_id'];folder=RAW/group/tid;result=load(folder/'result.json');previous=None
            check(result['task_id']==tid and len(result['attempts'])==result['attempt_count'],'result_structure',task_id=tid)
            check([a['stage'] for a in result['attempts']]==STAGES[:len(result['attempts'])],'stage_prefix',task_id=tid)
            check(result['library_size_before']==len(library),'library_size_before',task_id=tid)
            # Reproduce keyword overlap and stable first-best tie breaking exactly.
            words=set(catalog[tid]['prompt'].lower().split());best=None;bestscore=-1
            for item in library:
                overlap=len(set(item['snippet'].lower().split()) & words)
                if overlap>bestscore: best=item;bestscore=overlap
            context=('Example:\nProblem: '+best['snippet']+'\nSolution:\n'+best['solution']) if best and bestscore>3 else ''
            check(bool(context)==result['repair_skill_available'],'retrieval_available',task_id=tid)
            context_source=best['task_id'] if context else None
            for a in result['attempts']:
                stage=a['stage'];eid=tid+':'+stage;pos+=1
                cp=folder/(stage+'.py');rp=folder/(stage+'.response.json');vp=folder/(stage+'.verdict.json')
                code=cp.read_text();response=load(rp);verdict=load(vp);req=response['request'];prompt=req['messages'][-1]['content']
                t=catalog[tid]
                parts=['Solve this competitive programming problem in Python 3.10. Return the complete solution in one ```python``` block.','Problem:\n'+t['prompt']]
                if t['starter_code']:parts+=['Starter code / required signature:\n'+t['starter_code']]
                if t['function_name']:parts+=['Use the required function/method named '+t['function_name']+'. Preserve the required class and signature; do not read stdin.']
                else:parts+=['Write a complete program that reads standard input and prints the required output.']
                parts+=['Think carefully about correctness, edge cases and time/memory complexity.']
                base_prompt='\n\n'.join(parts)
                check(prompt.startswith(base_prompt) if stage in ['l3','l4'] else prompt==base_prompt,'base_prompt_contract',event_id=eid)
                codehash=sha(cp);key=(tid,stage);new=repaired[key];tv=trusted_verdicts.get(key)
                for expected in [a['code_sha256'],inventory[key]['sha256'],new['code_sha256']]: check(codehash==expected,'program_hash',event_id=eid)
                check(verdict['passed']==a['passed'] and verdict['feedback']==a['feedback'],'old_verdict',event_id=eid)
                check(response['usage']==a['usage'] and response['finish_reason']==a['finish_reason'],'response_summary',event_id=eid)
                match=re.search(r'```(?:python)?\s*\n(.*?)```',response['text'],re.S)
                extracted=match.group(1).lstrip('\n').rstrip() if match else response['text'].rstrip()
                check(code==extracted,'code_extraction',event_id=eid)
                def stamp(p):return metadata[str(p.relative_to(ROOT/'raw'))]['mtime_ns']
                response_ns=stamp(rp);verdict_ns=stamp(vp);result_ns=stamp(folder/'result.json');created_ns=response['created']*10**9
                check(created_ns<=response_ns<=verdict_ns<=result_ns,'timestamp_within_event',event_id=eid)
                if previous:
                    check(previous['verdict_written_ns']<=created_ns+10**9,'within_task_causality',event_id=eid)
                elif previous_result_ns is not None:
                    check(previous_result_ns<=created_ns+10**9,'within_stream_causality',event_id=eid)
                try: ast.parse(code);syntax='OK' if code.strip() else 'EMPTY'
                except SyntaxError:syntax='SYNTAX_ERROR'
                check(parse310[key]['code_sha256']==codehash and parse310[key]['syntax']==syntax,'python310_static_parse_crosscheck',event_id=eid)
                kind='PASS' if verdict['passed'] else ('INCOMPLETE_ARTIFACT' if not code.strip() else ('SYNTAX_ERROR' if syntax=='SYNTAX_ERROR' else 'UNRESOLVED_EXECUTION_OR_SEMANTICS'))
                root=verified.get(key)
                codes=verdict.get('result_codes',{})
                correct_categories=[]
                if task['dataset']=='lcb':
                    if codes.get('-2'):correct_categories.append('WRONG_ANSWER')
                    if codes.get('-3'):correct_categories.append('TIME_LIMIT')
                    if codes.get('-4'):correct_categories.append('EXECUTION_OR_TEST_FRAMEWORK_EXCEPTION_UNRESOLVED')
                mistranslated=task['dataset']=='lcb' and bool(codes.get('-2') or codes.get('-3'))
                if root: reliability='VERIFIED_IMPLEMENTATION_FAILURE_ON_INDEPENDENT_LEGAL_INPUT'
                elif not verdict['passed'] and syntax in ['EMPTY','SYNTAX_ERROR']:reliability='VERIFIED_ARTIFACT_FAILURE_NOT_ALGORITHM'
                elif tv and tv['passed']:reliability='PASS_ON_AUDITED_FINITE_SUITE'
                else: reliability='UNVERIFIED_BENCHMARK_VERDICT'
                # E1 labels concern a particular final-code/case pair, not every candidate in that task.
                card=e1.get(tid);card_exact=bool(card and card.get('source_code_sha256')==codehash)
                feedback_parent=previous['event_id'] if stage in ['l3','l4'] else None
                if feedback_parent:
                    suffix='\n\nPrevious candidate:\n```python\n'+previous['source_code']+'\n```\n\nVerifier feedback: '+previous['old_feedback']+'\nFix the solution and return the corrected complete Python program/function.'
                    if context:suffix+='\n\nReference from a previously solved problem:\n'+context
                    check(prompt.endswith(suffix),'repair_prompt_chain',event_id=eid)
                    edges.append({'source':feedback_parent,'target':eid,'type':'PREVIOUS_CODE_AND_OLD_FEEDBACK','feedback':previous['old_feedback'],'source_old_result_codes':previous['old_result_codes']})
                else: check('Previous candidate:\n```python\n' not in prompt,'independent_prompt_stage',event_id=eid)
                if stage in ['l3','l4'] and context:
                    check(best['completed_ns']<=created_ns+10**9 and best['task_id']!=tid,'retrieval_causality',event_id=eid)
                    edges.append({'source':best['final_event_id'],'target':eid,'type':'PREVIOUSLY_OLD_PASS_SOLUTION_REFERENCE','source_task':best['task_id'],'source_old_pass_trust':'NOT_INDEPENDENTLY_VERIFIED','context_sha256':digest(context)})
                event={'event_id':eid,'task_id':tid,'dataset':task['dataset'],'difficulty':task['difficulty'],'stream':group,'task_order':task['order'],'stream_event_index':pos,'stage':stage,
                  'api_created_utc':utc(created_ns),'response_written_utc':utc(response_ns),'verdict_written_utc':utc(verdict_ns),'verdict_written_ns':verdict_ns,
                  'time_basis':'original verdict file mtime; API created is request-era timestamp, not evaluation completion; file timestamps are observational evidence',
                  'code_sha256':codehash,'response_sha256':sha(rp),'verdict_sha256':sha(vp),'request_sha256':digest(json.dumps(req,sort_keys=True)),
                  'old_passed':verdict['passed'],'old_feedback':verdict['feedback'],'old_result_codes':verdict.get('result_codes',{}),
                  'retrospective_correct_code_categories':correct_categories,'known_feedback_category_mistranslation':mistranslated,
                  'repaired_status':new['status'],'repaired_epoch':new['epoch'],'repaired_input_coverage':new.get('input_coverage'),
                  'audited_suite_status':tv['status'] if tv else None,'audited_suite_case_scope':'finite independent legal suite only' if tv else None,
                  'retrospective_reliability':reliability,'artifact_syntax':syntax,'failure_kind':kind,
                  'finish_reason':response['finish_reason'],'model':response['model'],'usage':response['usage'],'latency_s':response['latency_s'],
                  'feedback_parent_event':feedback_parent,'retrieved_source_task':context_source if stage in ['l3','l4'] else None,
                  'retrieved_context_sha256':digest(context) if stage in ['l3','l4'] and context else None,
                  'root_family_retrospective':root['root_cause']['family'] if root else None,
                  'E1_exact_code_label':card['label'] if card_exact else None,'E1_task_level_context':card['label'] if card else None,
                  'prior_audit_task_symptom':audits.get(tid,{}).get('primary_observed_mechanism'),
                  'historical_failure_memory_entries':0,'historical_failure_verification_timestamp':None,
                  'paths':{'code':str(cp.relative_to(ROOT)),'response':str(rp.relative_to(ROOT)),'verdict':str(vp.relative_to(ROOT))}}
                events.append(event);previous={**event,'source_code':code}
            check(result['passed']==previous['old_passed'] and result['final_stage']==previous['stage'],'final_selection',task_id=tid)
            check(not any(x['passed'] for x in result['attempts'][:-1]),'stop_on_first_pass',task_id=tid)
            if result['passed']:
                library.append({'task_id':tid,'snippet':catalog[tid]['prompt'][:200],'solution':(folder/(result['final_stage']+'.py')).read_text()[:500],
                  'completed_ns':result_ns,'final_event_id':tid+':'+result['final_stage']})
            check(result['library_size_after']==len(library),'library_size_after',task_id=tid)
            previous_result_ns=result_ns
            memory_rows.append({'stream':group,'task_order':task['order'],'task_id':tid,'old_final_passed':result['passed'],
              'success_library_size_before':result['library_size_before'],'success_library_size_after':len(library),'retrieval_source':context_source,
              'historical_failure_library_size':0,'completed_ns':result_ns})
        saved=load(RAW/group/'library.json')
        check(set(saved['solutions'])=={x['task_id'] for x in library},'final_library_membership',stream=group)
        for item in library:
            source=next(x for x in events if x['event_id']==item['final_event_id']);p=ROOT/source['paths']['code']
            check(saved['solutions'][item['task_id']]==p.read_text(),'final_library_solution',task_id=item['task_id'])
        stream_rows.append({'stream':group,'tasks':len(metas),'programs':pos,'old_final_passes':len(library),'failure_memory_entries':0})
    assert len(events)==2132 and len({x['event_id'] for x in events})==2132
    events.sort(key=lambda e:(e['verdict_written_ns'],e['stream'],e['stream_event_index']))
    # Reconstructed global ordering is a deterministic merge of 8 streams, not a shared memory.
    for i,e in enumerate(events,1): e['global_event_index']=i
    jsonl('events.jsonl',events);jsonl('dependency_edges.jsonl',edges);jsonl('task_memory_replay.jsonl',memory_rows)
    save('streams.json',stream_rows);save('integrity_checks.json',{'checks':dict(checks),'issue_count':len(issues),'issues':issues})
    # Candidate mechanisms: diagnosis stays provisional unless supported by a legal witness.
    mechanisms={}
    def add(mid,e,confidence,description,promote=False):
        m=mechanisms.setdefault(mid,{'mechanism_id':mid,'confidence':confidence,'description':description,'eligible_for_algorithm_failure_memory':promote,'event_ids':[],'tasks':set(),'first_global_event':e['global_event_index']})
        m['event_ids'].append(e['event_id']);m['tasks'].add(e['task_id'])
    for e in events:
        if not e['old_passed']:
            if e['artifact_syntax']=='EMPTY':add('artifact_empty',e,'DIRECT_ARTIFACT','No executable historical artifact; not an algorithm mechanism.')
            if e['artifact_syntax']=='SYNTAX_ERROR':add('artifact_syntax',e,'DIRECT_STATIC_PARSE','Historical artifact fails Python parsing; not a semantic algorithm diagnosis.')
            if e['finish_reason']=='length':add('output_budget_exhaustion',e,'DIRECT_RESPONSE_METADATA','Response exhausted output budget; does not by itself prove this caused the failure.')
            if e['old_feedback']=='Wrong answer.':add('unresolved_wrong_answer',e,'UNRESOLVED','Old evaluator reported WA; legal input, oracle and comparator not fully certified.')
            if e['known_feedback_category_mistranslation']:add('LCB_feedback_category_mistranslation',e,'VERIFIED_CODE_TRANSLATION','LCB -2 means WA, -3 means timeout; old feedback mislabeled them. This does not certify the test or code.')
            if 'error' in e['old_feedback'].lower():add('unresolved_execution_error',e,'UNRESOLVED','Old coarse error category; compiler/runtime/framework cause not established.')
            if 'Time limit' in e['old_feedback']:add('unresolved_timeout',e,'UNRESOLVED','Runtime limit signal; algorithmic complexity versus input/framework remains unresolved.')
            if e['repaired_status']=='PASS':add('evaluation_rule_sensitive',e,'OBSERVED_RULE_DISAGREEMENT','Old failure became repaired PASS; repaired evaluation itself is not a truth oracle.')
            if e['audited_suite_status']=='PASS':add('old_failure_but_audited_suite_pass',e,'FINITE_SCOPE_ONLY','Old failure but passes independently audited finite inputs; not proof original failing input was invalid.')
            if e['E1_exact_code_label']=='VERIFIED_EVALUATION_PROBLEM':add('E1_exact_code_evaluation_problem',e,'PRIOR_CASE_REVIEW','Specific historical final code and case have an E1 evaluation/data finding; do not generalize to all inputs.')
        if e['root_family_retrospective']:
            add(e['root_family_retrospective'],e,'VERIFIED_LEGAL_WITNESS','Independent legal counterexample, observed exception and minimal counterfactual repair verified.',True)
    bank=[]
    for m in mechanisms.values():
        m['task_ids']=sorted(m.pop('tasks'));m['task_count']=len(m['task_ids']);m['event_count']=len(m['event_ids'])
        m['availability']='retrospective S0 certification only' if m['eligible_for_algorithm_failure_memory'] else 'shadow replay candidate; never certified root cause merely by grouping'
        if m['eligible_for_algorithm_failure_memory']:
            m['evidence_files']=['../trusted_rgf_20261020/counterfactuals/'+tid+'/' for tid in m['task_ids']]
            m['independent_mechanism_families']=1
        bank.append(m)
    save('mechanism_candidates.json',bank)
    # Shadow replay computes only contemporaneously observable features. No retrospective label is injected.
    curve=[]; seen_failed=set();seen_artifact=set();seen_verified_hindsight=set();seen_candidate=set();rawfails=0;artifact_events=0;hindsight_events=0;oldpass=0
    by_stream=collections.defaultdict(lambda:{'events':0,'failures':0,'tasks':set(),'candidates':set()})
    for e in events:
        if e['old_passed']:oldpass+=1
        else:
            rawfails+=1;seen_failed.add(e['task_id'])
            if e['artifact_syntax'] in ['EMPTY','SYNTAX_ERROR']:artifact_events+=1;seen_artifact.add(e['task_id'])
        if e['root_family_retrospective']:hindsight_events+=1;seen_verified_hindsight.add(e['task_id'])
        observable=[]
        if not e['old_passed']:
            observable.append('observed:'+e['old_feedback'])
            if e['artifact_syntax']!='OK':observable.append('static:'+e['artifact_syntax'])
            if e['finish_reason']=='length':observable.append('metadata:output_budget_exhaustion')
        seen_candidate.update(observable);s=by_stream[e['stream']];s['events']+=1;s['failures']+=not e['old_passed'];s['candidates'].update(observable)
        if not e['old_passed']:s['tasks'].add(e['task_id'])
        curve.append({'global_event_index':e['global_event_index'],'utc':e['verdict_written_utc'],'event_id':e['event_id'],'stream':e['stream'],
          'cumulative_old_failure_events':rawfails,'cumulative_old_failure_tasks':len(seen_failed),'cumulative_old_pass_events':oldpass,
          'shadow_static_artifact_failure_events':artifact_events,'shadow_static_artifact_failure_tasks':len(seen_artifact),'shadow_observable_candidate_types':len(seen_candidate),
          'historically_certified_functional_failure_tasks':0,'hindsight_verified_functional_failure_tasks':len(seen_verified_hindsight),
          'stream_event_index':s['events'],'stream_failure_events':s['failures'],'stream_failure_tasks':len(s['tasks']),'stream_observable_candidate_types':len(s['candidates'])})
    table('online_accumulation.csv',curve)
    save('replay_policy.json',{'new_model_calls':0,'candidate_execution_in_S0':0,'streams':8,
      'global_order':'verdict-file-mtime merge; metadata is observational, not a signed event log; tie break stream and local order',
      'failure_available_after':'old verdict file write; retrieval availability checked against earlier same-stream completed task',
      'shadow_candidate_policy':'only old feedback, finish_reason, empty/parse status from the current or earlier event',
      'retrospective_truth':'independent legal suite, E1 and two witnesses are overlays, never historically available memory',
      'actual_historical_failure_memory':0,'strict_verified_online_curve':0,
      'same_task_reuse':'previous-code repair edges allowed and explicitly separated from cross-task references',
      'cross_stream_retrieval':False,'future_event_retrieval':False})
    all_transitions=[]; trusted_regressions=[]
    for tid in catalog:
        es=sorted((e for e in events if e['task_id']==tid),key=lambda e:STAGES.index(e['stage']))
        for a,b in zip(es,es[1:]):
            row={'task_id':tid,'from':a['event_id'],'to':b['event_id'],'direct_repair':b['feedback_parent_event']==a['event_id'],
              'old':str(a['old_passed'])+'->'+str(b['old_passed']),'repaired':a['repaired_status']+'->'+b['repaired_status'],
              'audited':str(a['audited_suite_status'])+'->'+str(b['audited_suite_status'])}
            all_transitions.append(row)
            if a['audited_suite_status']=='PASS' and b['audited_suite_status'] not in [None,'PASS']:trusted_regressions.append(row)
    table('candidate_transitions.csv',all_transitions);save('audited_suite_regressions.json',trusted_regressions)
    stats={'tasks':800,'programs':2132,'old_pass_events':oldpass,'old_failure_events':rawfails,'tasks_with_any_old_failure':len(seen_failed),
      'old_final_failure_tasks':sum(not load(p)['passed'] for p in RAW.glob('*/*/result.json')),
      'artifact_fail_events':artifact_events,'artifact_fail_tasks':len(seen_artifact),'verified_functional_failure_events_retrospective':hindsight_events,
      'verified_functional_failure_tasks_retrospective':len(seen_verified_hindsight),'actual_historical_failure_memory':0,
      'repair_prompt_edges':sum(x['type']=='PREVIOUS_CODE_AND_OLD_FEEDBACK' for x in edges),
      'reference_prompt_edges':sum(x['type']=='PREVIOUSLY_OLD_PASS_SOLUTION_REFERENCE' for x in edges),
      'old_feedback_counts':dict(collections.Counter(e['old_feedback'] for e in events)),
      'repaired_status_counts':dict(collections.Counter(e['repaired_status'] for e in events)),
      'reliability_counts':dict(collections.Counter(e['retrospective_reliability'] for e in events)),
      'old_fail_repaired_pass':sum(not e['old_passed'] and e['repaired_status']=='PASS' for e in events),
      'old_pass_repaired_fail':sum(e['old_passed'] and e['repaired_status']!='PASS' for e in events),
      'audited_suite_covered_programs':len(trusted_verdicts),'audited_suite_regressions':len(trusted_regressions),
      'known_feedback_category_mistranslation_events':sum(e['known_feedback_category_mistranslation'] for e in events),
      'mistranslated_feedback_actually_consumed_edges':sum(next(e for e in events if e['event_id']==x['source'])['known_feedback_category_mistranslation'] for x in edges if x['type']=='PREVIOUS_CODE_AND_OLD_FEEDBACK'),
      'verdict_timestamp_ties':len(events)-len({e['verdict_written_ns'] for e in events}),
      'integrity_issue_count':len(issues),'models':dict(collections.Counter(e['model'] for e in events)),
      'first_verdict_utc':events[0]['verdict_written_utc'],'last_verdict_utc':events[-1]['verdict_written_utc'],'new_model_calls':0}
    save('summary.json',stats)
    plot(curve,group_tasks)
    report(stats,bank,stream_rows,issues,trusted_regressions)
    inputs=[*SOURCE.glob('*'),*RAW.rglob('*.json'),*RAW.rglob('*.py')]
    save('source_hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(inputs) if p.is_file()})
    supporting=[BASE/'repair_v2/catalog.json',BASE/'trusted_rgf_20261020/inventory_2132.json',
      BASE/'repair_v2/epochs/repaired_reports_20261020/candidate_results.json',BASE/'e1_e2_20261020/e1_cards_final.json',
      BASE/'逐题机制审计.json',trusted/'failure_mechanism_bank.json',trusted/'validation.json',trusted/'input_contract_review.json',
      *list((trusted/'verdicts').glob('*/*.json')),*list((trusted/'counterfactuals').glob('*/*'))]
    save('supporting_evidence_hashes.json',{str(p.relative_to(BASE)):sha(p) for p in sorted(supporting) if p.is_file()})
    print(json.dumps(stats,ensure_ascii=False,indent=2))
def plot(curve,groups):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
    fig,ax=plt.subplots(1,2,figsize=(12,4.3),layout='constrained');x=[r['global_event_index'] for r in curve]
    for key,label in [('cumulative_old_failure_events','Old evaluator failure events'),('cumulative_old_failure_tasks','Tasks with an old failure'),('shadow_static_artifact_failure_events','Static artifact failure events')]:ax[0].plot(x,[r[key] for r in curve],label=label)
    ax[0].set(xlabel='Merged historical candidate index',ylabel='Cumulative count',title='Observed failures and artifact signals');ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
    ax[1].step(x,[r['hindsight_verified_functional_failure_tasks'] for r in curve],where='post',label='Hindsight: verified implementation defects')
    ax[1].plot(x,[0]*len(x),label='Actually certified during original run',linestyle='--');ax[1].set(xlabel='Merged historical candidate index',ylabel='Independent tasks',title='Certification is retrospective');ax[1].set_yticks([0,1,2]);ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
    fig.savefig(ROOT/'online_failure_accumulation.png',dpi=180);fig.savefig(ROOT/'online_failure_accumulation.svg');plt.close(fig)
    fig,axes=plt.subplots(2,4,figsize=(14,6),layout='constrained')
    for ax,group in zip(axes.flat,sorted(groups)):
        rows=[r for r in curve if r['stream']==group];ax.plot([r['stream_event_index'] for r in rows],[r['stream_failure_events'] for r in rows]);ax.set(title=group,xlabel='Local event',ylabel='Old failure events');ax.grid(alpha=.2)
    fig.savefig(ROOT/'per_stream_accumulation.png',dpi=150);plt.close(fig)
def report(s,bank,streams,issues,regressions):
    lines=['# E3-S0：历史失败事件流与时间顺序回放','',
      '完成800题、2,132份历史程序的离线事件重建；未调用模型，也未重新执行候选程序。结果基于全部原始请求/响应/判定与已有重评分、逐题审查证据。','',
      f"原评测失败事件{s['old_failure_events']}个，涉及{s['tasks_with_any_old_failure']}道题；最终失败{s['old_final_failure_tasks']}题。它们是观测失败信号，不能直接视为真实算法错误。原运行中的失败机制库大小始终为0，实际积累并复用的是旧评测判成功的解。",'',
      '## 事件与时间','',
      '每份历史程序形成一个事件，保留task/stage、源码哈希、请求/响应/判定哈希、旧反馈与错误码、原始时间戳、模型成本、修复父节点、成功解引用来源，以及事后可信性覆盖。原始created是请求时期时间；判定可用时刻采用服务器原始verdict文件mtime。该mtime为观察证据而非签名日志，未把归档解压时间当历史时间。','',
      '8条dataset×difficulty题流独立顺序处理；跨流按判定mtime稳定合并，仅用于画总曲线，不模拟一个跨流共享库。同秒/重叠API请求不代表严格全序因果；因果结论以流内顺序与实际请求内容为准。','',
      f"逐项检查源码与3份独立清单哈希、响应提取结果、判定一致性、阶段顺序、时间偏序、成功即停止、库容量和检索内容。共有{len(issues)}条未通过检查，详见 integrity_checks.json。",'',
      '## 历史信息回放','',
      'l1/l2a/l2b属于重新生成；l3/l4才收到上一候选及旧反馈。成功库按同流此前旧PASS题的题面前200字符做词重叠检索，引用解答前500字符。逐条复现检索算法并核对原始请求后缀。l3只收到l2b、l4只收到l3，不能把此前所有失败都算作模型已获得的信息。','',
      f"恢复{s['repair_prompt_edges']}条上一候选/反馈边和{s['reference_prompt_edges']}条前序成功解引用边；所有来源与目标保留在dependency_edges.jsonl。引用来源的旧PASS并不保证其全输入域正确。",'',
      f"LCB错误码解释另行核对：{s['known_feedback_category_mistranslation_events']}个事件存在-2/-3误译，其中{s['mistranslated_feedback_actually_consumed_edges']}条误译反馈实际进入l3/l4。-4仍保留程序/框架异常歧义，不擅自改成算法错误。误译检查只确认反馈语义，不证明输入和标准答案可信。",'',
      '## 可信性分层','', '|证据层|事件数|','|---|---:|']
    for k,v in s['reliability_counts'].items():lines.append(f'|{k}|{v}|')
    lines += ['', f"静态可确证的空/语法错误产物共{s['artifact_fail_events']}次，涉及{s['artifact_fail_tasks']}题；它们是产物失败，不是功能算法机制。可信有限测试只覆盖155份程序。其余旧WA/异常不因重新评分后仍失败就升级为算法失败。",'',
      'E1证据只有当源码哈希精确匹配时标记到事件；其他阶段仅保留题级背景。旧失败新PASS和旧PASS新失败仅标为规则敏感。时间上，E1/可信集证据均来自事后，绝不写入历史时刻的真实机制库。','',
      f"新旧规则敏感：旧失败→重评分PASS {s['old_fail_repaired_pass']}次；旧PASS→重评分非PASS {s['old_pass_repaired_fail']}次。两种评分都不是完全认证的真值。",'',
      '## 在线积累曲线','',
      '![在线积累](online_failure_accumulation.png)','',
      '左图：随历史候选到达累积的旧失败事件、失败题数和静态产物失败。右图：事后证据投影出的2个真实实现缺陷，与原运行当时已认证机制数0分开显示。在线shadow候选只读取当前及更早反馈、截断元数据和静态语法；不读取未来阶段、后验标签、后续修复或隐藏反例。','',
      f"合并时发现{s['verdict_timestamp_ties']}个纳秒时间戳并列，按流名及流内序号稳定排序；不据此推断跨流先后因果。",'',
      '因此右图的2条增量不能称为历史运行当时发现了2个机制。它们只有在事后独立证据到位后才可用于未来实验。online_accumulation.csv同时保存全局和8条流的逐事件计数；per_stream_accumulation.png提供分流曲线。','',
      '## 机制候选库','', '|候选|事件数|独立题数|证据|可进入算法失败机制库|','|---|---:|---:|---|---|']
    for m in bank:lines.append(f"|{m['mechanism_id']}|{m['event_count']}|{m['task_count']}|{m['confidence']}|{'事后可用' if m['eligible_for_algorithm_failure_memory'] else '否'}|")
    lines += ['', '候选可重叠，行数不能相加当独立失败数。WA、超时、错误反馈、预算耗尽是待核查的信号/候选类别，不自动是算法根因。唯一达到合法反例+实际异常+局部反事实修复门槛的仍是阶乘表容量不足与长链递归资源不足，两者属于实现缺陷。没有新增确证的算法选择或状态转移机制。','',
      f"可信集连续候选出现PASS→非PASS {len(regressions)}次（见audited_suite_regressions.json）。只有direct_repair=true才是直接修复边；即便如此，该指标仅说明有限测试退化，不能仅凭相邻阶段就证明后续修复改坏了原本全域正确的算法。",'',
      '## 8条独立题流','', '|题流|题数|程序数|旧最终PASS|原失败库|','|---|---:|---:|---:|---:|']
    for x in streams:lines.append(f"|{x['stream']}|{x['tasks']}|{x['programs']}|{x['old_final_passes']}|0|")
    lines += ['', '## 输出与复核','',
      '- events.jsonl：2,132个候选事件；dependency_edges.jsonl：实际信息流。',
      '- online_accumulation.csv：逐事件累积；两张PNG和总览SVG。',
      '- mechanism_candidates.json：候选、证据等级、来源事件及准入状态。',
      '- task_memory_replay.jsonl：800题的成功库重建。',
      '- integrity_checks.json / source_hashes.json：一致性与原始文件摘要。',
      '- candidate_transitions.csv：全部1,332条同题相邻候选变化。',
      '- replay_policy.json：时间、信息隔离与事后证据策略。',
      '- raw/runs：全部原始程序、请求、响应、判定与结果；不含API密钥。','',
      '本轮不开展新修复、重新评分或因果效应试验。S0给出的机制候选需要独立合法反例审查后才能升级；不能用症状聚类数量代替可信机制数量。', '']
    lines += ['两个已验证机制各仅有1道来源题，尚无跨题复现证据，不能声称已建立可迁移机制规律。其余10类是分诊候选或评分问题，不是10种已验证算法机制。','',
      '这两个缺陷均来自l1中间候选，原运行后来分别在taco_0875的l3、abc301_f的l2a得到旧PASS；它们不是312道旧最终失败题中新增确证的两个终态失败。失败事件流覆盖所有尝试，因此能保留此类被最终成功掩盖的历史失败。','',
      '独立复核脚本verify_replay.py进一步检查所有来源文件哈希、1,264条依赖边，并仅用允许的当时可见字段重算全部2,132个前缀，结果见replay_verification.json。Python3.10原运行环境静态解析全部程序，与本地解析分类一致；没有执行候选。','']
    (ROOT/'E3-S0报告.md').write_text('\n'.join(lines))
if __name__=='__main__': main()
