import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        p = [0] * (n + 1)
        for i in range(1, n + 1):
            p[i] = data[idx]
            idx += 1

        h = [0] * (n + 1)
        for i in range(1, n + 1):
            h[i] = data[idx]
            idx += 1

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            x = data[idx]
            y = data[idx + 1]
            idx += 2
            adj[x].append(y)
            adj[y].append(x)

        parent = [0] * (n + 1)
        parent[1] = -1

        order = []
        stack = [1]

        while stack:
            u = stack.pop()
            order.append(u)

            for v in adj[u]:
                if v == parent[u]:
                    continue
                parent[v] = u
                stack.append(v)

        subtree_sum = p[:]

        for u in reversed(order):
            if u != 1:
                subtree_sum[parent[u]] += subtree_sum[u]

        good = [0] * (n + 1)
        ok = True

        for u in range(1, n + 1):
            val = subtree_sum[u] + h[u]

            if val < 0 or val % 2 != 0:
                ok = False
                break

            g = val // 2

            if g < 0 or g > subtree_sum[u]:
                ok = False
                break

            good[u] = g

        if ok:
            child_good_sum = [0] * (n + 1)

            for u in range(2, n + 1):
                child_good_sum[parent[u]] += good[u]

            for u in range(1, n + 1):
                if good[u] < child_good_sum[u]:
                    ok = False
                    break

        answers.append("YES" if ok else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()