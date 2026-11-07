"""Build private DEV references from the frozen split and independent exact checks."""
import argparse
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read, save


def independent_results():
    # These are offline host checks for fixed DEV references, never model input.
    post = Fraction(1, 2)**3 / (Fraction(1, 2)**3 + Fraction(1, 3)**3)
    ks = {2013*a*(s-a)//s for s in range(2,2014) if 2013%s==0
          for a in range(1,s) if math.gcd(a,s)==1}
    # With u=-x,v=-2y, objective=45+(u+v-7)^2+(uv-4)^2/4.
    # The roots of z²-7z+4 are real, so both squares can vanish.
    minimum = Fraction(45)
    edges = [(0,1),(0,2),(1,0),(2,0)]
    bad = 0
    for k in range(1,5):
        for fixed in combinations(edges,k):
            rows, cols = map(set,zip(*fixed))
            if len(rows)==len(cols)==k:
                bad += (-1)**(k+1)*sum((-1)**j*math.comb(101-len(rows|cols),j)
                                       *math.factorial(101-k-j)
                                       for j in range(102-len(rows|cols)))
    derangements = sum((-1)**j*math.comb(101,j)*math.factorial(101-j) for j in range(102))
    secret = Fraction(round(Fraction(derangements-bad,derangements)*100000),100000)
    primes = [p for p in range(101,500) if all(p%d for d in range(2,math.isqrt(p)+1))
              and 2016%(p-1)>100 and 2*(2016%(p-1)-21)==p-1
              and (pow(2,2016,p)+pow(2,21,p))%p==0]
    assert len(primes)==1
    seq = [Fraction(1),Fraction(1),Fraction(2,3)]
    while seq[-1]>Fraction(1,10**6):
        a,b,c = seq[-3:]
        seq.append(c*c*b/(2*b*b-c*a))

    def partitionable(n):
        divisors = [d for d in range(n,0,-1) if n%d==0]
        total = sum(divisors)
        if total%3 or n>total//3:
            return False
        def fill(index, bins):
            if index==len(divisors):
                return True
            d = divisors[index]
            for space in set(bins):
                if space>=d:
                    remaining = list(bins)
                    remaining[remaining.index(space)] -= d
                    if fill(index+1,remaining):
                        return True
            return False
        return fill(0,[total//3]*3)

    least = next(n for n in range(1,121) if partitionable(n))
    return dict(zip((2531,620,2140,2395,461,2598,2511,2508),
                    (post,len(ks),minimum,secret,primes[0],len(seq),10**5,least)))


def prepare(split, output):
    manifest = read(split/'data_split_manifest.json')
    tasks = read(split/'dev/tasks.json')
    scoring = read(split/'dev/scoring.private.json')
    expected = independent_results()
    rows = [r for r in manifest['rows'] if r['split']=='DEV']
    if len(rows)!=len(tasks) or len(tasks)!=len(scoring) or len(rows)!=len(expected):
        raise PermissionError('unexpected DEV coverage')
    reviewed = []
    for row, task, ref in zip(rows,tasks,scoring):
        digest = fingerprint(task['problem'])
        if (row['task_id']!=task['task_id'] or task['task_id']!=ref['task_id']
                or digest!=row['statement_hash'] or digest!=ref['problem_sha256']
                or fingerprint(ref)!=row['scoring_reference_id']):
            raise PermissionError('DEV reference check failed: '+row['task_id'])
        independent = Fraction(expected[row['source_row']])
        agrees = independent==Fraction(ref['gold_answer'])
        reviewed.append(dict(task_id=task['task_id'],problem_sha256=digest,
                             reference_id=fingerprint(ref),answer=ref['gold_answer'] if agrees else None,
                             independent_answer=str(independent),
                             status='REFERENCE_VERIFIED' if agrees else 'REFERENCE_CONFLICT',
                             applicability='CANDIDATE_REVIEW_REQUIRED'))
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    save(output,dict(manifest_sha256=manifest['manifest_sha256'],rows=reviewed))
    output.chmod(0o400)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    prepare(args.split,args.output)
