import sys
from bisect import bisect_right


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        b = next(it)
        a = [next(it) for _ in range(n)]

        if k == 0:
            cnt_ge = sum(1 for x in a if x >= b)

            if cnt_ge == 0:
                answers.append("1")
            else:
                ans = cnt_ge
                if cnt_ge < n:
                    ans += 1
                answers.append(str(ans))
            continue

        a.sort()

        coords = []
        last = None
        for x in a:
            if x != last:
                coords.append(x)
                last = x

        m = len(coords)
        rank = {x: i + 1 for i, x in enumerate(coords)}
        tree = [0] * (m + 1)

        ans = 0

        for x in a:
            threshold = (x - b) // k
            idx = bisect_right(coords, threshold)

            best = 0
            i = idx
            while i > 0:
                if tree[i] > best:
                    best = tree[i]
                i -= i & -i

            dp = best + 1
            if dp > ans:
                ans = dp

            i = rank[x]
            while i <= m:
                if dp > tree[i]:
                    tree[i] = dp
                i += i & -i

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()