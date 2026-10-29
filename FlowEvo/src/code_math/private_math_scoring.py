"""Host-only exact rational / normalized symbolic-text score, after answer lock.
Never send this object or its private rows to a solver, compiler or Worker.
"""
import re,time
from fractions import Fraction
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore

VERSION='math-private-exact-rational-text-v1'

def extract_answer(text):
    if not isinstance(text,str):raise TypeError('answer text required')
    starts=[m.end() for m in re.finditer(r'\\boxed\s*\{',text)]
    if starts:
        start=starts[-1];depth=1
        for i in range(start,len(text)):
            if text[i]=='{':depth+=1
            elif text[i]=='}':depth-=1
            if not depth:return text[start:i].strip()
    matches=list(re.finditer(r'(?im)^\s*(?:the\s+)?(?:final\s+)?answer\s*(?:is\s*|:\s*)([^\n]+)',text))
    if matches:return matches[-1].group(1).strip().rstrip('.')
    return text.strip().split('\n')[-1].strip() if text.strip() else ''

def normalized(text):
    s=extract_answer(text).strip().strip('$').strip().rstrip('.')
    s=s.replace('\\left','').replace('\\right','').replace('\\dfrac','\\frac').replace('\\tfrac','\\frac')
    s=re.sub(r'\s+','',s)
    # Commas are removed only within integer numeral grouping, not vectors/sets.
    if re.fullmatch(r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?',s):s=s.replace(',','')
    frac=re.fullmatch(r'(-?)\\frac\{(-?\d+)\}\{(-?\d+)\}',s)
    if frac:s=('-' if frac[1] else '')+frac[2]+'/'+frac[3]
    if re.fullmatch(r'-?\d+(?:/[-+]?\d+|\.\d+)?',s):
        try:return ('rational',str(Fraction(s)))
        except (ZeroDivisionError,ValueError):pass
    return ('text',s)

def answer_equal(predicted,gold):
    return bool(predicted.strip()) and normalized(predicted)==normalized(gold)

class PrivateMathScorer:
    def __init__(self,private_rows,controller_journal,score_journal):
        self._rows={r['task_id']:r for r in private_rows};self.controller=EvidenceStore(controller_journal);self.events=EvidenceStore(score_journal)

    def score(self,task,locked):
        raw={k:v for k,v in locked.items() if k!='locked_sha256'}
        if fingerprint(raw)!=locked.get('locked_sha256') or task.task_id!=locked.get('task_id'):raise ValueError('answer lock mismatch')
        receipts=[r for r in self.controller.records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']==locked]
        if not receipts:raise PermissionError('private score requires durable terminal answer lock')
        prior=[r['payload'] for r in self.events.records() if r['payload'].get('episode_id')==locked['episode_id']]
        if prior:return prior[0]
        row=self._rows[task.task_id]
        if row['problem_sha256']!=fingerprint(task.problem):raise ValueError('private scorer task binding')
        matched=answer_equal(locked['final_output'],row['gold_answer'])
        numeric_pair=normalized(locked['final_output'])[0]=='rational' and normalized(row['gold_answer'])[0]=='rational'
        score_class='MATCH' if matched else ('EXACT_RATIONAL_MISMATCH' if numeric_pair else 'UNVERIFIED_NONMATCH')
        result=dict(score_class=score_class,credible_failure=score_class=='EXACT_RATIONAL_MISMATCH',episode_id=locked['episode_id'],task_id=task.task_id,locked_sha256=locked['locked_sha256'],
            correct=answer_equal(locked['final_output'],row['gold_answer']),scorer_version=VERSION,
            visibility='HOST_POST_TASK_ONLY',gold_exposed=False)
        self.events.append('MATH_PRIVATE_SCORE',result,time.time());return result
