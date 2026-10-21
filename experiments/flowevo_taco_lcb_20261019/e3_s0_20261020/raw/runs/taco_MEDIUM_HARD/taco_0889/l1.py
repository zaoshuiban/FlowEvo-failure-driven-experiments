import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        p = data[idx:idx + n]
        idx += n

        h = data[idx:idx + n]
        idx += n

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            x = data[idx] - 1
            y = data[idx + 1] - 1
            idx += 2
            adj[x].append(y)
            adj[y].append(x)

        parent = [-1] * n
        order = [0]

        for v in order:
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                order.append(u)

        subtree_size = p[:]

        for i in range(n - 1, 0, -1):
            v = order[i]
            subtree_size[parent[v]] += subtree_size[v]

        good = [0] * n
        ok = True

        for v in range(n):
            total = subtree_size[v]
            value = total + h[v]

            if value < 0 or value % 2 != 0:
                ok = False

            g = value // 2

            if g < 0 or g > total:
                ok = False

            good[v] = g

        if ok:
            child_good_sum = [0] * n

            for i in range(n - 1, -1, -1):
                v = order[i]

                if child_good_sum[v] > good[v]:
                    ok = False
                    break

                if parent[v] != -1:
                    child_good_sum[parent[v]] += good[v]

        answers.append("YES" if ok else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()