import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

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
            par = parent[u]
            if par > 0:
                subtree_sum[par] += subtree_sum[u]

        good = [0] * (n + 1)
        possible = True

        for u in range(1, n + 1):
            value = subtree_sum[u] + h[u]

            if value % 2 != 0:
                possible = False
                break

            good_count = value // 2

            if good_count < 0 or good_count > subtree_sum[u]:
                possible = False
                break

            good[u] = good_count

        if possible:
            child_good_sum = [0] * (n + 1)

            for u in reversed(order):
                if child_good_sum[u] > good[u]:
                    possible = False
                    break

                par = parent[u]
                if par > 0:
                    child_good_sum[par] += good[u]

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()