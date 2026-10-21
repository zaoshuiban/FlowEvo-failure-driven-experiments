import sys
from collections import deque
from math import gcd


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ptr = 1
    output = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        a = data[ptr:ptr + n]
        ptr += n

        prv = [(i - 1) % n for i in range(n)]
        nxt = [(i + 1) % n for i in range(n)]
        alive = [True] * n

        q = deque()

        # Initially Arkady is listening to song 0. The next songs are
        # 1, 2, ..., n - 1, 0.
        for v in range(1, n):
            p = v - 1
            if gcd(a[p], a[v]) == 1:
                q.append((p, v))

        p = n - 1
        v = 0
        if gcd(a[p], a[v]) == 1:
            q.append((p, v))

        answer = []
        remaining = n

        while q and remaining > 0:
            p, v = q.popleft()

            if not alive[v] or prv[v] != p:
                continue

            if gcd(a[p], a[v]) != 1:
                continue

            answer.append(v + 1)
            alive[v] = False
            remaining -= 1

            if remaining == 0:
                break

            w = nxt[v]

            nxt[p] = w
            prv[w] = p

            # After a song is deleted, the next song cannot be deleted
            # immediately. It will be considered again after one full cycle.
            if gcd(a[p], a[w]) == 1:
                q.append((p, w))

        line = [str(len(answer))]
        line.extend(map(str, answer))
        output.append(" ".join(line))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()