import sys


class DSU:
    __slots__ = ("parent", "size")

    def __init__(self, n):
        self.parent = list(range(n + 1))
        self.size = [1] * (n + 1)

    def find(self, x):
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m1 = next(it)
    m2 = next(it)

    dsu1 = DSU(n)
    dsu2 = DSU(n)

    for _ in range(m1):
        u = next(it)
        v = next(it)
        dsu1.union(u, v)

    for _ in range(m2):
        u = next(it)
        v = next(it)
        dsu2.union(u, v)

    answer = []

    for u in range(1, n + 1):
        for v in range(u + 1, n + 1):
            if dsu1.find(u) != dsu1.find(v) and dsu2.find(u) != dsu2.find(v):
                answer.append((u, v))
                dsu1.union(u, v)
                dsu2.union(u, v)

    output = [str(len(answer))]
    output.extend(f"{u} {v}" for u, v in answer)

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()