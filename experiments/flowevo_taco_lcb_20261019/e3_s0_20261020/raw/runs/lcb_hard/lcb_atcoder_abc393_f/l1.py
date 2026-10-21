import sys
from bisect import bisect_left, bisect_right


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    Q = next(it)

    A = [next(it) for _ in range(N)]

    queries = []
    for qi in range(Q):
        R = next(it)
        X = next(it)
        queries.append((R, X, qi))

    values = sorted(set(A))
    M = len(values)

    # dp[i] = length of LIS ending at A[i]
    dp = [0] * N
    bit = [0] * (M + 1)

    for i, a in enumerate(A):
        less_count = bisect_left(values, a)

        best = 0
        idx = less_count
        while idx > 0:
            if bit[idx] > best:
                best = bit[idx]
            idx -= idx & -idx

        cur = best + 1
        dp[i] = cur

        idx = less_count + 1
        while idx <= M:
            if cur > bit[idx]:
                bit[idx] = cur
            idx += idx & -idx

    # Answer queries offline by increasing R
    queries.sort()
    bit2 = [0] * (M + 1)
    ans = [0] * Q

    pos = 0
    for R, X, qi in queries:
        while pos < R:
            a = A[pos]
            cur = dp[pos]
            idx = bisect_left(values, a) + 1

            while idx <= M:
                if cur > bit2[idx]:
                    bit2[idx] = cur
                idx += idx & -idx

            pos += 1

        limit = bisect_right(values, X)

        best = 0
        idx = limit
        while idx > 0:
            if bit2[idx] > best:
                best = bit2[idx]
            idx -= idx & -idx

        ans[qi] = best

    print("\n".join(map(str, ans)))


if __name__ == "__main__":
    solve()