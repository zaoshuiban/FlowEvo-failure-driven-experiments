import sys
from functools import lru_cache

@lru_cache(maxsize=None)
def calc(n, m):
    if n == 0 or m == 0:
        return 0

    even_count = (m + 1) // 2
    odd_count = m // 2

    if n & 1:
        p = n // 2
        return m - calc(p, even_count) - calc(p + 1, odd_count)
    else:
        p = n // 2
        return calc(p, even_count) + calc(p, odd_count)


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2
        ans.append(str(calc(n, m)))

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()