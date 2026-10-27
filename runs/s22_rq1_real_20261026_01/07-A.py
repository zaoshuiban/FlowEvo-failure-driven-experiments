import sys
from math import gcd
from collections import deque

def solve():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    out_lines = []

    for _ in range(t):
        n = int(data[idx]); idx += 1
        a = list(map(int, data[idx:idx+n])); idx += n

        if n == 1:
            if a[0] == 1:
                out_lines.append("1 1")
            else:
                out_lines.append("0")
            continue

        prev = [(i - 1) % n for i in range(n)]
        nxt = [(i + 1) % n for i in range(n)]
        deleted = [False] * n
        q = deque()

        # Initial check: song i is deletable if gcd(a[prev[i]], a[i]) == 1
        for i in range(n):
            if gcd(a[prev[i]], a[i]) == 1:
                q.append(i)

        res = []

        while q:
            i = q.popleft()
            if deleted[i]:
                continue
            p = prev[i]
            if deleted[p]:
                continue
            if gcd(a[p], a[i]) == 1:
                deleted[i] = True
                res.append(i + 1)
                nx = nxt[i]
                nxt[p] = nx
                prev[nx] = p
                # After deletion, the next song nx may become deletable
                if not deleted[nx] and gcd(a[p], a[nx]) == 1:
                    q.append(nx)

        if res:
            out_lines.append(str(len(res)) + " " + " ".join(map(str, res)))
        else:
            out_lines.append("0")

    sys.stdout.write("\n".join(out_lines))

if __name__ == "__main__":
    solve()