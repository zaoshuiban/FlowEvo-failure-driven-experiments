import sys
from collections import deque
from math import gcd


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    output = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        a = data[pos:pos + n]
        pos += n

        nxt = [(i + 1) % n for i in range(n)]
        alive = [True] * n
        q = deque(range(n))

        deleted = []

        while q:
            i = q.popleft()

            if not alive[i]:
                continue

            j = nxt[i]

            if gcd(a[i], a[j]) == 1:
                alive[j] = False
                deleted.append(j + 1)

                if i == j:
                    continue

                nxt[i] = nxt[j]
                q.append(i)

        if deleted:
            output.append(str(len(deleted)) + " " + " ".join(map(str, deleted)))
        else:
            output.append("0")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()