import sys
from math import gcd


class Fenwick:
    __slots__ = ("n", "bit")

    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)

    def add(self, i, delta):
        n = self.n
        bit = self.bit
        while i <= n:
            bit[i] += delta
            i += i & -i

    def prefix_sum(self, i):
        s = 0
        bit = self.bit
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    def kth(self, k):
        idx = 0
        bit = self.bit
        n = self.n
        step = 1 << (n.bit_length() - 1)

        while step:
            nxt = idx + step
            if nxt <= n and bit[nxt] < k:
                idx = nxt
                k -= bit[nxt]
            step >>= 1

        return idx + 1


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

        a = [0] * (n + 1)
        for i in range(1, n + 1):
            a[i] = data[pos]
            pos += 1

        nxt = [0] * (n + 1)
        prv = [0] * (n + 1)

        for i in range(1, n + 1):
            nxt[i] = i + 1 if i < n else 1
            prv[i] = i - 1 if i > 1 else n

        fw = Fenwick(n)
        bad = [False] * (n + 1)

        for i in range(1, n + 1):
            if gcd(a[i], a[nxt[i]]) == 1:
                bad[i] = True
                fw.add(i, 1)

        ans = []
        active = n
        start = 1

        while active > 0:
            total = fw.prefix_sum(n)
            if total == 0:
                break

            before = fw.prefix_sum(start - 1)

            if total > before:
                u = fw.kth(before + 1)
            else:
                u = fw.kth(1)

            v = nxt[u]
            ans.append(v)

            if active == 1:
                active = 0
                break

            p = prv[v]
            q = nxt[v]

            if bad[v]:
                bad[v] = False
                fw.add(v, -1)

            nxt[p] = q
            prv[q] = p
            active -= 1

            new_bad = gcd(a[p], a[nxt[p]]) == 1

            if bad[p] != new_bad:
                if new_bad:
                    fw.add(p, 1)
                else:
                    fw.add(p, -1)
                bad[p] = new_bad

            start = q

        if ans:
            output.append(str(len(ans)) + " " + " ".join(map(str, ans)))
        else:
            output.append("0")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()