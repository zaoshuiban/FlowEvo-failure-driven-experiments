import sys
from array import array


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = data[1:1 + t]
    if not queries:
        return

    max_n = max(queries)

    # H[i] = 1 + 1/2 + ... + 1/i, computed with Kahan summation
    # for better precision when H[r] - H[l-1] is needed.
    H = array('d', [0.0]) * (max_n + 1)
    s = 0.0
    c = 0.0
    for i in range(1, max_n + 1):
        y = 1.0 / i - c
        t_sum = s + y
        c = (t_sum - s) - y
        s = t_sum
        H[i] = s

    ans = array('d', [0.0]) * (max_n + 1)

    # m is the first index with positive probability in the optimal distribution.
    m = 1

    for N in range(1, max_n + 1):
        while True:
            M = N - m + 1
            Hval = H[N] - H[m - 1]
            lam = (M - 2.0) / Hval

            if lam >= m:
                m += 1
            elif m > 1 and lam < m - 1:
                m -= 1
            else:
                break

        M = N - m + 1
        Hval = H[N] - H[m - 1]

        # Expected score = (sum_{i=m}^N i - (M-2)^2 / Hval) / 2
        S1 = (m + N) * M / 2.0
        expected = (S1 - (M - 2.0) * (M - 2.0) / Hval) / 2.0

        max_score = 2.0 * N - 1.0
        ans[N] = expected / max_score

    out = [f"{ans[n]:.11f}" for n in queries]
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()