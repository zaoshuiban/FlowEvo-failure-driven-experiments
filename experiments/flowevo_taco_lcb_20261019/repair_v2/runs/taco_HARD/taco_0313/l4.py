import sys
from math import gcd
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    output = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        nxt = [(i + 1) % n for i in range(n)]
        deleted = [False] * n
        q = deque()

        for i in range(n):
            if gcd(a[i], a[nxt[i]]) == 1:
                q.append(i)

        ans = []

        while q:
            x = q.popleft()

            if deleted[x]:
                continue

            y = nxt[x]

            if gcd(a[x], a[y]) == 1:
                ans.append(y + 1)
                deleted[y] = True
                nxt[x] = nxt[y]

                if x != y:
                    q.append(x)

        if ans:
            output.append(str(len(ans)) + " " + " ".join(map(str, ans)))
        else:
            output.append("0")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()