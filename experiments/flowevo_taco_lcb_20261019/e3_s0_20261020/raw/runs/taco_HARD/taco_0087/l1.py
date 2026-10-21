import sys
from bisect import bisect_right

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        k = next(it)
        b = next(it)

        A = [next(it) for _ in range(N)]

        if k == 0:
            cnt_high = 0
            has_low = 0

            for x in A:
                if x >= b:
                    cnt_high += 1
                else:
                    has_low = 1

            if cnt_high == 0:
                answers.append("1")
            else:
                answers.append(str(cnt_high + has_low))
            continue

        A.sort()

        uniq = []
        for x in A:
            if not uniq or uniq[-1] != x:
                uniq.append(x)

        m = len(uniq)
        pos = {v: i + 1 for i, v in enumerate(uniq)}

        bit = [0] * (m + 1)
        ans = 1

        for v in A:
            limit = (v - b) // k

            if limit < 0:
                idx = 0
            else:
                idx = bisect_right(uniq, limit)

            best = 0
            j = idx
            while j > 0:
                if bit[j] > best:
                    best = bit[j]
                j -= j & -j

            dp = best + 1
            if dp > ans:
                ans = dp

            j = pos[v]
            while j <= m:
                if dp > bit[j]:
                    bit[j] = dp
                j += j & -j

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()