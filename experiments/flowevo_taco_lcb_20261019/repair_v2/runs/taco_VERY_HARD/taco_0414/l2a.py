import sys
from bisect import bisect_left

INF = 10**9


def calc(qS, qD, oS, oD, K):
    """
    For every query strength qS[i] (winner from one child),
    add the minimum cost to also make qS[i] beat some winner from the other child.
    """
    m = len(qS)
    n = len(oS)
    res = [0] * m

    low = 0
    high = -1
    pref = INF

    dq = []
    head = 0

    for i in range(m):
        q = qS[i]

        # Opponents weaker than q: q beats them naturally, cost +0.
        while low < n and oS[low] <= q:
            val = oD[low]
            if val < pref:
                pref = val
            low += 1

        # Opponents q can bribe to beat: q < strength <= q + K, cost +1.
        limit = q + K
        while high + 1 < n and oS[high + 1] <= limit:
            high += 1
            val = oD[high]
            while len(dq) > head and oD[dq[-1]] >= val:
                dq.pop()
            dq.append(high)

        while head < len(dq) and dq[head] < low:
            head += 1

        best = pref
        if head < len(dq):
            cand = oD[dq[head]] + 1
            if cand < best:
                best = cand

        old = qD[i]
        if old >= INF or best >= INF:
            res[i] = INF
        else:
            val = old + best
            res[i] = val if val < INF else INF

    return res


def merge_blocks(left, right, K):
    LS, LD = left
    RS, RD = right

    newLD = calc(LS, LD, RS, RD, K)
    newRD = calc(RS, RD, LS, LD, K)

    nl = len(LS)
    nr = len(RS)
    S = [0] * (nl + nr)
    D = [0] * (nl + nr)

    i = j = idx = 0

    while i < nl and j < nr:
        if LS[i] < RS[j]:
            S[idx] = LS[i]
            D[idx] = newLD[i]
            i += 1
        else:
            S[idx] = RS[j]
            D[idx] = newRD[j]
            j += 1
        idx += 1

    while i < nl:
        S[idx] = LS[i]
        D[idx] = newLD[i]
        i += 1
        idx += 1

    while j < nr:
        S[idx] = RS[j]
        D[idx] = newRD[j]
        j += 1
        idx += 1

    return S, D


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        H = next(it)
        K = next(it)
        N = 1 << H

        strengths = [next(it) for _ in range(N)]

        blocks = []

        # Process the first stage directly.
        for i in range(0, N, 2):
            a = strengths[i]
            b = strengths[i + 1]

            if a > b:
                dp_a = 0
                dp_b = 1 if a - b <= K else INF
            else:
                dp_b = 0
                dp_a = 1 if b - a <= K else INF

            if a < b:
                blocks.append(([a, b], [dp_a, dp_b]))
            else:
                blocks.append(([b, a], [dp_b, dp_a]))

        while len(blocks) > 1:
            new_blocks = []
            for i in range(0, len(blocks), 2):
                new_blocks.append(merge_blocks(blocks[i], blocks[i + 1], K))
            blocks = new_blocks

        finalS, finalD = blocks[0]
        pos = bisect_left(finalS, strengths[0])
        ans = finalD[pos]

        answers.append(str(-1 if ans >= INF else ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()