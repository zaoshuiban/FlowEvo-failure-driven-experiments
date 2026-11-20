"""Read-only Route C supplements: prior probes, context loss, full case appendices.

Prior researcher probes remain retrospective evaluation data, never inputs to
prefix_signals or a model. This module performs no new environment interaction.
"""
from collections import Counter
from pathlib import Path
import json
import audit_alfworld_route_c_failures as C

A=C.A
PRIOR=Path.home()/'.local/share/flowevo/alfworld_online120_diagnostics_20261109_01'


def prior_probes(episodes):
    manifest=A.read(PRIOR/'artifact_integrity.json')
    for name,sha in manifest['files'].items():
        if A.sha(PRIOR/name)!=sha:raise PermissionError('prior probe changed: '+name)
    results=[]
    for ep in episodes:
        if ep['won']:continue
        path=PRIOR/f"failure_{ep['sequence']:03}.json";old=A.read(path)
        if old['task_id']!=ep['task_id'] or old['steps']!=ep['steps'] or old['initial']!=ep['initial']:
            raise PermissionError('prior original trace differs')
        branches=[(path,old['probe']['alternative'],'FIRST_RESEARCHER_BRANCH')]
        for prefix in ('followup','shortcut'):
            path=PRIOR/f"{prefix}_{ep['sequence']:03}.json"
            if path.exists():branches.append((path,A.read(path)['result'],A.read(path)['policy']))
        for path,b,policy in branches:
            anchor=b['fork']-1
            if not b['alternate_steps']:raise ValueError('empty historical probe')
            expected=ep['initial']['commands'] if anchor==0 else ep['steps'][anchor-1]['feedback']['commands']
            if b['alternate_steps'][0]['legal_before']!=expected:raise PermissionError('probe prefix mismatch')
            if anchor+len(b['alternate_steps'])>50:raise PermissionError('historical probe exceeded source budget')
            for i,s in enumerate(b['alternate_steps']):
                if s['feedback']['action'] not in s['legal_before']:raise PermissionError('illegal old probe action')
                if i and s['legal_before']!=b['alternate_steps'][i-1]['feedback']['commands']:raise PermissionError('probe transition missing')
            if b['won']!=b['alternate_steps'][-1]['feedback']['won']:raise PermissionError('probe success mismatch')
            results.append(dict(sequence=ep['sequence'],file=path.name,sha256=A.sha(path),role='HOST_RETROSPECTIVE_REPAIR_ONLY',
                anchor=anchor,steps=len(b['alternate_steps']),won=b['won'],policy=policy,
                prior_probe_location_used=any(t in policy for t in ('prior','earlier','first public probe')),
                original_prefix_receipts_match=True,legal_chain_complete=True,
                actions=[x['feedback']['action'] for x in b['alternate_steps']],new_execution=False))
    return dict(archive_sha256=A.sha(PRIOR/'artifact_integrity.json'),files_verified=len(manifest['files']),
                original_failed_steps_compared=sum(len(e['steps']) for e in episodes if not e['won']),branches=results)


def native_prompt_visibility(ep):
    facts=[]
    for s in ep['steps']:
        if not s['requested']:continue
        i=s['step'];wire=s['requested']['wire'];user=wire['messages'][-1]['content']
        history=ep['steps'][:i-1];shown=history[-10:]
        # Presence checks use exact raw messages; excerpts can also be repeated
        # elsewhere, so inclusion is not a proof that a model remembered them.
        if shown:
            expected='\nRecent actions:\n'+'\n'.join('  > '+x['feedback']['action']+'\n    '+x['feedback']['observation'][:120] for x in shown)
            if expected not in user:raise PermissionError('native history format changed')
        facts.append(dict(step=i,request_id=s['requested']['request_id'],wire_sha256=A.digest(wire),
            transmitted_history_steps=[x['step'] for x in shown],omitted_prior_history_steps=[x['step'] for x in history[:-10]],
            observation_truncation_chars=120,
            l2_injected=s['decision']['l2_injected'],l3_injected=s['decision']['l3_injected'],
            provider_finish_reason=s['requested']['provider_response']['choices'][0]['finish_reason']))
    return facts


def appendix(ep,prompt_rows):
    lines=[f"# Route C 原始失败证据：第{ep['sequence']}局",'',
        '仅历史开发数据。以下逐步内容来自原环境与模型回执，不包含事后探针。',
        f"\n来源ID：{ep['task_id']}；目标：{ep['goal']}；原状态：{ep['status']}。",'']
    for s in ep['steps']:
        lines.extend([f"## 步骤 {s['step']}",'',f"执行者：{s['decision']['source']}；L1/L2/L3：{s['decision']['l1_executed']}/{s['decision']['l2_injected']}/{s['decision']['l3_injected']}。",
            '\n动作：`'+s['feedback']['action']+'`','\n观察：\n```text\n'+s['feedback']['observation']+'\n```',
            '\n当步合法动作：\n```json\n'+json.dumps(s['legal_actions'],ensure_ascii=False)+'\n```'])
        if s['requested']:
            lines.extend(['\n模型原始正文：\n```text\n'+s['requested']['output']+'\n```',
                          '\n请求ID：`'+s['requested']['request_id']+'`'])
        lines.extend(['\n公开状态摘要（可不完整）：\n```json\n'+json.dumps(s['state_after'],ensure_ascii=False)+'\n```',
            '\n原回执哈希：`'+s['receipt_sha256']+'`',''])
    path=C.OUT/f"Case_{ep['sequence']:03}.private.md";text='\n'.join(lines)+'\n'
    if path.exists() and path.read_text()!=text:raise PermissionError('immutable appendix')
    if not path.exists():path.write_text(text)
    return dict(path=path.name,sha256=A.sha(path),steps=len(ep['steps']))


def main():
    C.verify();episodes=A.read(C.OUT/'episodes.private.json');prior=prior_probes(episodes)
    prompt={str(e['sequence']):native_prompt_visibility(e) for e in episodes}
    details=[appendix(e,prompt[str(e['sequence'])]) for e in episodes if not e['won']]
    out=dict(scope='READ_ONLY_SUPPORTING_AUDIT',source_input_sha256=A.sha(C.OUT/'episodes.private.json'),
        audit_revision=2,supersedes='Supporting_Evidence.private.json',
        correction='Prior-location provenance includes explicit first public probe wording; no branch results changed.',
        prior_probe_audit=prior,prompt_visibility=prompt,appendices=details,
        all_finish_reasons=dict(Counter(p['provider_finish_reason'] for rows in prompt.values() for p in rows)),
        new_model_calls=0,new_environment_steps=0,new_worker_calls=0,
        model_training_allowed_paths=[],original_trace_reconstruction='RAW_NATIVE_RECEIPTS_NOT_PRIOR_PROBE_SUMMARIES')
    A.commit(C.OUT/'Supporting_Evidence_v2.private.json',out)
    return out


if __name__=='__main__':
    r=main();print(dict(old_probe_branches=len(r['prior_probe_audit']['branches']),
        archived_files_verified=r['prior_probe_audit']['files_verified'],original_steps=r['prior_probe_audit']['original_failed_steps_compared'],finish_reasons=r['all_finish_reasons']))
