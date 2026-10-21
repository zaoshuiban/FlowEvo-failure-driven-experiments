import sys
from bisect import bisect_left


def solve() -> None:
    data = sys.stdin.buffer.read()
    ndata = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < ndata and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < ndata and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    output = []

    for _ in range(t):
        n = next_int()

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        p = [0] * (n + 1)
        time = [0] * (n + 1)
        for i in range(1, n + 1):
            u = next_int()
            p[i] = u
            time[u] = i

        a = [0] * (n + 1)
        for i in range(1, n + 1):
            a[i] = next_int()

        b = [0] * (n + 1)
        for i in range(1, n + 1):
            b[i] = next_int()

        dsu_parent = [0] * (n + 1)
        recon_parent = [0] * (n + 1)

        def find(x):
            while dsu_parent[x] != x:
                dsu_parent[x] = dsu_parent[dsu_parent[x]]
                x = dsu_parent[x]
            return x

        for day in range(n, 0, -1):
            u = p[day]
            dsu_parent[u] = u

            for v in adj[u]:
                if time[v] > day:
                    root = find(v)
                    if root != u:
                        recon_parent[root] = u
                        dsu_parent[root] = u

        root = p[1]

        children = [[] for _ in range(n + 1)]
        for v in range(1, n + 1):
            parent = recon_parent[v]
            if parent:
                children[parent].append(v)

        ans = [-1] * (n + 1)
        prefix = []
        path = []
        stack = [(root, 0)]

        while stack:
            u, state = stack.pop()

            if state == 0:
                current_sum = a[u]
                if prefix:
                    current_sum += prefix[-1]

                prefix.append(current_sum)
                path.append(u)

                if current_sum >= b[u]:
                    pos = bisect_left(prefix, b[u])
                    ans[u] = time[path[pos]]

                stack.append((u, 1))

                for v in children[u]:
                    stack.append((v, 0))

            else:
                prefix.pop()
                path.pop()

        output.append(" ".join(str(ans[i]) for i in range(1, n + 1)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()