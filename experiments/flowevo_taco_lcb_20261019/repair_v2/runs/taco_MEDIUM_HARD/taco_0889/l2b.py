import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        p = [0] * (n + 1)
        for i in range(1, n + 1):
            p[i] = next(it)

        h = [0] * (n + 1)
        for i in range(1, n + 1):
            h[i] = next(it)

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            x = next(it)
            y = next(it)
            adj[x].append(y)
            adj[y].append(x)

        parent = [0] * (n + 1)
        parent[1] = -1
        order = [1]

        idx = 0
        while idx < len(order):
            u = order[idx]
            idx += 1

            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    order.append(v)

        subtree_sum = p[:]

        for u in reversed(order):
            if parent[u] > 0:
                subtree_sum[parent[u]] += subtree_sum[u]

        possible = True
        good = [0] * (n + 1)

        for u in range(1, n + 1):
            value = subtree_sum[u] + h[u]

            if value % 2 != 0:
                possible = False
                continue

            good_count = value // 2

            if good_count < 0 or good_count > subtree_sum[u]:
                possible = False

            good[u] = good_count

        if possible:
            children_good_sum = [0] * (n + 1)

            for u in reversed(order):
                if children_good_sum[u] > good[u]:
                    possible = False
                    break

                if parent[u] > 0:
                    children_good_sum[parent[u]] += good[u]

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()