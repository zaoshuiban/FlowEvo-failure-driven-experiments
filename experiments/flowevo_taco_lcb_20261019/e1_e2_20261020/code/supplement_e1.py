"""Independent post-review proof, no model API and no E2 response access."""
import functools,itertools,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def offset(word):
 x=0
 for c in word:x=-x if c=='A' else 2-x
 return x
@functools.lru_cache(None)
def matching(s):
 if not s:return True
 if len(s)%2:return False
 return any(s[0]==s[j] and matching(s[1:j]) and matching(s[j+1:]) for j in range(1,len(s),2))
def main():
 count=0
 for n in range(0,11):
  for chars in itertools.product('AB',repeat=n):
   word=''.join(chars)
   if matching(word):assert len(word)%2==0 and offset(word)==0
   count+=1
 p=ROOT/'private_e1/taco_0604';case=json.loads((p/'private_failure_case.json').read_text());words=case['input'].split();assert int(words[0])==len(words)-1;witnesses=[{'length':len(w),'reflection_offset':offset(w)} for w in words[1:]]
 assert all(x['reflection_offset']!=0 for x in witnesses)
 assert json.loads((p/'isolated_failure_execution.json').read_text())['output'].strip()=='0'
 proof={'task_id':'taco_0604','independent_oracle_result':0,'provided_reference':case['expected'],'witnesses':witnesses,'exhaustive_necessary_condition_checks':count,'proof':'Assign A the reflection f(x)=-x and B the reflection g(x)=2-x. Both are involutions. A noncrossing perfect matching contains an adjacent matched pair; remove it and induct. Every such matched word must compose to identity, hence send 0 to 0. All ten input words send 0 to nonzero values, so none can have such a matching. This is a necessary-condition proof independent of the candidate stack implementation.','e1_model_calls':0}
 (p/'independent_reflection_proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 cards=json.loads((ROOT/'e1_cards.json').read_text())
 for c in cards:
  if c['task_id']=='taco_0604':
   c.update(label='VERIFIED_EVALUATION_PROBLEM',root_subtype='wrong_reference',finding='独立反射复合不变量证明十个词均不可能有非交叉完全匹配，正确计数为 0，参考 1 错。',independent_evidence=proof,root_cause_certainty='confirmed specific defect')
  if c['task_id']=='taco_0910':c.update(root_subtype='reference_case_format',finding='题面要求 YES/NO；图含 1-2、2-3 而缺 1-3，因此 NO 正确；参考 No 与规定的输出格式不同。不声称题面明确允许任意大小写。')
  if c['task_id']=='taco_0291':c['additional_evidence']='Prior l3 candidate passes all 93 audited legal hidden cases; final syntax-invalid candidate shows observed-test repair degradation, without asserting universal correctness.'
 (ROOT/'e1_cards_final.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2)+'\n')
 from collections import Counter
 summary={'tasks':93,'counts':dict(Counter(x['label'] for x in cards)),'by_sampling_group':{g:dict(Counter(x['label'] for x in cards if x['sampling_group']==g)) for g in ['persistent_wa','exceptions','rescued_pass','regressed_wa']},'root_subtype_counts':dict(Counter(x['root_subtype'] for x in cards)),'new_model_calls_for_e1':0,'review_revision':'Initial e1_cards.json preserved; independent proof resolves taco_0604 and reference-case wording corrected. E2 checkpoint selection unchanged.'}
 (ROOT/'e1_summary_final.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 for c in cards:
  p=ROOT/'private_e1'/c['task_id'];text=(p/'证据卡.md').read_text()
  if c['task_id'] in ['taco_0604','taco_0910','taco_0291']:
   (p/'补充复核.md').write_text('# 补充复核\n\n'+c['finding']+'\n\n'+str(c.get('independent_evidence'))+'\n\n'+str(c.get('additional_evidence',''))+'\n')
 print(summary)
if __name__=='__main__':main()
