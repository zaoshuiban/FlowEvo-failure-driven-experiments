import sys
from bisect import bisect_left


def int_iter(data):
    i = 0
    n = len(data)
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


def find_root(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def solve():
    data = sys.stdin.buffer.read()
    it = int_iter(data)

    try:
        t = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(it)

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next(it)
            v = next(it)
            adj[u].append(v)
            adj[v].append(u)

        p = [0] * n
        pos = [0] * (n + 1)

        for i in range(n):
            x = next(it)
            p[i] = x
            pos[x] = i + 1

        a = [0] * (n + 1)
        for i in range(1, n + 1):
            a[i] = next(it)

        b = [0] * (n + 1)
        for i in range(1, n + 1):
            b[i] = next(it)

        # Build the elimination tree by adding vertices in reverse removal order.
        children = [[] for _ in range(n + 1)]
        active = bytearray(n + 1)

        dsu_parent = [0] * (n + 1)
        dsu_size = [0] * (n + 1)
        comp_top = [0] * (n + 1)

        for idx in range(n - 1, -1, -1):
            x = p[idx]
            active[x] = 1
            dsu_parent[x] = x
            dsu_size[x] = 1
            comp_top[x] = x

            for y in adj[x]:
                if not active[y]:
                    continue

                rx = find_root(dsu_parent, x)
                ry = find_root(dsu_parent, y)

                if rx == ry:
                    continue

                top_y = comp_top[ry]
                children[x].append(top_y)

                if dsu_size[rx] < dsu_size[ry]:
                    dsu_parent[rx] = ry
                    dsu_size[ry] += dsu_size[rx]
                    comp_top[ry] = x
                else:
                    dsu_parent[ry] = rx
                    dsu_size[rx] += dsu_size[ry]
                    comp_top[rx] = x

        root = p[0]

        ans = [0] * (n + 1)

        path_nodes = []
        prefix_sum = []
        stack = [(root, 0)]

        while stack:
            u, state = stack.pop()

            if state == 0:
                current_sum = a[u] + (prefix_sum[-1] if prefix_sum else 0)
                prefix_sum.append(current_sum)
                path_nodes.append(u)

                idx = bisect_left(prefix_sum, b[u])
                if idx < len(prefix_sum):
                    ans[u] = pos[path_nodes[idx]]
                else:
                    ans[u] = -1

                stack.append((u, 1))

                for v in reversed(children[u]):
                    stack.append((v, 0))

            else:
                prefix_sum.pop()
                path_nodes.pop()

        answers.append(" ".join(str(ans[i]) for i in range(1, n + 1)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()