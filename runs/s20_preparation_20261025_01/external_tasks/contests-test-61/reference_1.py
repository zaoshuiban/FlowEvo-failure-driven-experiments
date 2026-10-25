import sys

IS_INTERACTIVE = False
input = input  # type: ignore

# input: function
if not IS_INTERACTIVE:
    *data, = sys.stdin.read().split("\n")[::-1]

    def input():  # type: ignore
        return data.pop()

def fprint(*args, **kwargs):
    print(*args, **kwargs, flush=True)

def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

'''
1 1
2 1
2 2
2 4
3 4

1-2-5
1-3-5
1-4-5



'''



def naive(topics, diffs):
    n = len(topics)
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if len({topics[i], topics[j], topics[k]}) == 3 or len({diffs[i], diffs[j], diffs[k]}) == 3:
                    cnt += 1
    return cnt


def fast(topics, diffs):
    tcnt = [0] * (n + 1)
    dcnt = [0] * (n + 1)
    for t, d in zip(topics, diffs):
        tcnt[t] += 1
        dcnt[d] += 1
    pairs = list(zip(topics, diffs))

    ans = n * (n - 1) * (n - 2) // 6
    for i in range(n):
        c0 = tcnt[topics[i]]
        c1 = dcnt[diffs[i]]
        c0 -= 1
        c1 -= 1
        if c0 and c1:
            ans -= c0 * c1

    return ans


'''
    n! / (n - 3)! / (3!)

    5 * 4 * 3

    1 2
    1 3
    2 2
'''

for _ in range(int(input())):
    n = int(input())
    topics = []
    diffs = []
    for _ in range(n):
        t, d = map(int, input().split())
        topics.append(t)
        diffs.append(d)

    print(fast(topics, diffs))



