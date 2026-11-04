"""Official-reference validation bank, NOT synthetic originals or operator permissions."""
import json,re,collections
from pathlib import Path
from audit_math_stream200_sources import ROOT,OUT,DATA,save,sha,grams

# Role selected by tournament date, before any target-model execution.
# Host-only answers transcribed from separately hashed organizer solutions.
SELECT={
 'feb-algnt':{1:('103','divisor sum'),2:('3375','digit equation unique integer'),4:('-984','floor sum'),5:('890','minimal polynomial evaluation difference'),9:('1037','interpolation coefficient modulo prime')},
 'feb-comb':{1:('56','constrained permutation count'),2:('29','disconnected vertex-subset count'),3:('105','unlabeled partition count'),4:('2304','self-avoiding path count'),5:('200','maximum closed trail length'),6:('6300','disjoint rectangle-pair count'),8:('2025/101','expected distinct-value count')},
 'nov-gen':{2:('12','minimum cyclic sequence length'),3:('1296','grid filling count'),4:('31','number of admissible polynomial levels'),6:('81920','self-avoiding path count'),7:('1305','minimum divisor count'),10:('372','maximum number of joint reachable states')},
 'nov-thm':{2:('5','triple intersection cardinality'),4:('99774','alphametic unique integer'),7:('7350','product of orbit frequencies'),9:('91/6','optimal expected stopping time')},
}
TRANSCRIPT={
('feb-algnt',2):r'Mark writes the expression $\sqrt{\overline{abcd}}$, where $\overline{abcd}$ is a four-digit number and $a\ne0$. Derek moves the digit a outside the radical, giving $a\sqrt{\overline{bcd}}$. The two expressions are equal. Compute the only possible four-digit number $\overline{abcd}$.',
('feb-algnt',4):r'Let $\lfloor z\rfloor$ denote the greatest integer less than or equal to z. Compute $\sum_{j=-1000}^{1000}\left\lfloor\frac{2025}{j+0.5}\right\rfloor$.',
('feb-algnt',5):r'Let S be the set of all nonconstant monic polynomials P with integer coefficients satisfying $P(\sqrt3+\sqrt2)=P(\sqrt3-\sqrt2)$. If Q is an element of S with minimal degree, compute the only possible value of Q(10)-Q(0).',
('feb-algnt',9):r'Let f be the unique polynomial of degree at most 2026 such that for each integer n in {1,...,2027}, f(n)=1 if n is a perfect square and f(n)=0 otherwise. Write the coefficient of $x^{2025}$ as a/b with coprime integers a,b. Compute the unique integer r in {0,...,2026} such that a-rb is divisible by 2027. Note that 2027 is prime.',
('nov-gen',3):'Ashley fills each cell of a 3 by 3 grid with some of the numbers 1, 2, 3, and 4 (possibly none or several). Compute the number of ways she can do so such that each row and each column contains each of 1, 2, 3, and 4 exactly once.',
('nov-gen',4):r'Given integers a,b,c with $c\le2025$ such that $|x^2+ax+b|=c$ has exactly 3 distinct integer solutions for x, compute the number of possible values of c.',
('nov-thm',4):r'Compute the unique 5-digit integer EARTH satisfying HATER + HEART = EARTH in base ten. The digits E,A,R,T,H are not necessarily distinct, but the leading digits E and H must be nonzero.',
}

def build():
    bank=OUT/'bank';public={};records=[];scores={};funnel=[]
    for round,selected in SELECT.items():
        key='gate-hmmt-2025-'+round
        src=OUT/'private/sources'
        pr=json.loads((src/(key+'-problems.receipt.json')).read_text());sr=json.loads((src/(key+'-solutions.receipt.json')).read_text())
        pages=json.loads((src/(key+'-problems.pages.json')).read_text());full='\n'.join(pages)
        mm=list(re.finditer(r'(?m)^(\d{1,2})\. ',full));items={int(m[1]):full[m.end():mm[j+1].start() if j+1<len(mm) else len(full)].strip() for j,m in enumerate(mm)}
        for n in range(1,11):
            tid=f'hmmt-2025-{round}-{n}';role='Development' if round.startswith('feb') else 'Gate'
            reason='SELECTED_OFFICIAL_SCALAR_REFERENCE' if n in selected else 'OUT_OF_THREE_DOMAIN_SCOPE_OR_NOT_SELECTED_IN_BOUNDED_POOL'
            if round=='nov-thm' and n in (1,5):reason='OFFICIAL_MULTIPLE_INTERPRETATIONS_OR_ACCEPTED_FORMS_REQUIRE_SEPARATE_SCORING_REVIEW'
            funnel.append(dict(task_id=tid,role=role,decision=reason))
            if n not in selected:continue
            problem=TRANSCRIPT.get((round,n),items[n]);problem=re.sub(r'©2025 HMMT','',problem).strip()
            answer,goal=selected[n];oid=f'HMMT/2025/{round.replace("-","/")}/P{n}'
            public[tid]=dict(task_id=tid,problem=problem)
            record=dict(task_id=tid,source_original_id=oid,lineage_id=oid,parameter_variant_id='ORIGINAL_PARAMETERS',mechanism_family='UNASSIGNED_CANDIDATE_SPECIFIC',
                dataset_role=role,goal_description=goal,problem_sha256=sha(problem.encode()),provenance_status='ARCHIVE_ITEM_VERIFIED',
                source=dict(url=pr['url'],sha256=pr['sha256'],item=str(n),page=1),answer_source=dict(url=sr['url'],sha256=sr['sha256']),
                transcription='HOST_MATH_LAYOUT_TRANSCRIPTION' if (round,n) in TRANSCRIPT else 'PDF_TEXT_WITH_LINE_BREAKS',
                validation_status='OFFICIAL_REFERENCE_BACKED_NOT_OPERATOR_VALIDATED',semantic_label='PENDING_ARTIFACT_SPECIFIC_REVIEW',
                no_target_model_calls=True,publication_date='2025-02-15' if role=='Development' else '2025-11-08')
            records.append(record);scores[tid]=dict(answer=answer,answer_source=record['answer_source'],problem_sha256=record['problem_sha256'])
    save(bank/'manifest.json',records);save(bank/'funnel.json',funnel)
    save(bank/'Development.public.json',[public[r['task_id']] for r in records if r['dataset_role']=='Development'])
    save(bank/'private/Gate.questions.json',[public[r['task_id']] for r in records if r['dataset_role']=='Gate'])
    save(bank/'private/scores.json',scores)
    # Exposure scan: fixed prior inventory + full frozen raw Omni-MATH (conservative reference).
    texts=[];inventory=[]
    paths={Path(x['path']) for x in json.loads((DATA/'audit/exposure_inventory.json').read_text()) if x.get('status')=='SCANNED'}
    paths|={DATA/'private/Omni-Math.jsonl',DATA/'public/tasks.jsonl'}
    def walk(x,path):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('problem','prompt') and isinstance(v,str) and len(v)>40:texts.append((str(path),v))
                elif isinstance(v,(dict,list)):walk(v,path)
        elif isinstance(x,list):
            for v in x:walk(v,path)
    for p in sorted(paths):
        if not p.exists():inventory.append(dict(path=str(p),status='MISSING'));continue
        b=p.read_bytes();inventory.append(dict(path=str(p),sha256=sha(b),status='SCANNED'))
        try:
            if p.suffix=='.jsonl':
                for l in b.decode().splitlines():walk(json.loads(l),p)
            else:walk(json.loads(b),p)
        except (ValueError,UnicodeError) as e:inventory[-1]['status']='PARSE_FAILED'
    dedup={sha(t.encode()):(p,t,grams(t)) for p,t in texts};screen=[]
    for tid,t in public.items():
        g=grams(t['problem']);rank=[]
        for h,(p,txt,gg) in dedup.items():
            coverage=len(g&gg)/max(1,len(g));precision=len(g&gg)/max(1,len(gg))
            if coverage>=.2:rank.append(dict(path=p,problem_sha256=h,coverage=coverage,precision=precision,problem=txt))
        screen.append(dict(task_id=tid,exact_hash_match=sha(t['problem'].encode()) in dedup,candidates=sorted(rank,key=lambda x:-(x['coverage']+x['precision']))[:3]))
    save(bank/'private/exposure_candidates.json',screen);save(bank/'exposure_inventory.json',inventory)
    save(bank/'screen_summary.json',dict(reference_files=len(inventory),unique_question_texts=len(dedup),exact_matches=sum(x['exact_hash_match'] for x in screen),near_review_required=sum(bool(x['candidates']) for x in screen),
        scope='Prior project exposure inventory plus all4428 Omni records; not a proof against all historical contest adaptations.',paid_model_calls=0))
    print('bank',len(records),'roles',dict(collections.Counter(r['dataset_role'] for r in records)))
if __name__=='__main__':build()
