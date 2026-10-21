import sys
from math import gcd


def read_ints():
    data = sys.stdin.buffer.read()
    n = len(data)
    i = 0
    while i < n:
        while i < n and data[i] <= 32:
            i += 1
        if i >= n:
            break
        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1
        yield num


def solve():
    it = iter(read_ints())
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            a = next(it) - 1
            b = next(it) - 1
            adj[a].append(b)
            adj[b].append(a)

        values = [next(it) for _ in range(n)]

        parent = [-1] * n
        parent[0] = -2
        order = [0]

        for v in order:
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                order.append(u)

        subtree_gcd = values[:]

        for v in reversed(order):
            p = parent[v]
            if p >= 0:
                subtree_gcd[p] = gcd(subtree_gcd[p], subtree_gcd[v])

        outside_gcd = [0] * n

        for v in order:
            children = []
            for u in adj[v]:
                if parent[u] == v:
                    children.append(u)

            m = len(children)
            if m == 0:
                continue

            prefix = [0] * (m + 1)
            current_gcd = 0

            for i, child in enumerate(children):
                current_gcd = gcd(current_gcd, subtree_gcd[child])
                prefix[i + 1] = current_gcd

            base = gcd(values[v], outside_gcd[v])
            suffix_gcd = 0

            for i in range(m - 1, -1, -1):
                child = children[i]
                other_gcd = gcd(prefix[i], suffix_gcd)
                outside_gcd[child] = gcd(base, other_gcd)
                suffix_gcd = gcd(suffix_gcd, subtree_gcd[child])

        answer = 0

        for v in range(n):
            damage = outside_gcd[v]

            for u in adj[v]:
                if parent[u] == v:
                    damage += subtree_gcd[u]

            if damage > answer:
                answer = damage

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()