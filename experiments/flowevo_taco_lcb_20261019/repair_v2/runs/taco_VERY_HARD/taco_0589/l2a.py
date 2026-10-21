import sys
from bisect import bisect_left


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    outputs = []

    for _ in range(t):
        n = next_int()

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        P = [0] * (n + 1)
        pos = [0] * (n + 1)

        for day in range(1, n + 1):
            u = next_int()
            P[day] = u
            pos[u] = day

        A = [0] * (n + 1)
        for i in range(1, n + 1):
            A[i] = next_int()

        B = [0] * (n + 1)
        for i in range(1, n + 1):
            B[i] = next_int()

        children = [[] for _ in range(n + 1)]

        active = bytearray(n + 1)
        dsu = list(range(n + 1))
        size = [0] * (n + 1)
        component_root = [0] * (n + 1)

        def find(x):
            while dsu[x] != x:
                dsu[x] = dsu[dsu[x]]
                x = dsu[x]
            return x

        for day in range(n, 0, -1):
            u = P[day]

            active[u] = 1
            dsu[u] = u
            size[u] = 1
            component_root[u] = u

            for v in adj[u]:
                if not active[v]:
                    continue

                ru = find(u)
                rv = find(v)

                if ru == rv:
                    continue

                rv_root = component_root[rv]
                children[u].append(rv_root)

                if size[ru] < size[rv]:
                    ru, rv = rv, ru

                dsu[rv] = ru
                size[ru] += size[rv]
                component_root[ru] = u

        root = P[1]
        ans = [-1] * (n + 1)

        path_sums = []
        path_days = []
        stack = [(root, 0)]

        while stack:
            u, state = stack.pop()

            if state == 0:
                path_days.append(pos[u])

                current_sum = A[u]
                if path_sums:
                    current_sum += path_sums[-1]
                path_sums.append(current_sum)

                if current_sum >= B[u]:
                    index = bisect_left(path_sums, B[u])
                    ans[u] = path_days[index]

                stack.append((u, 1))

                for child in reversed(children[u]):
                    stack.append((child, 0))

            else:
                path_sums.pop()
                path_days.pop()

        outputs.append(" ".join(str(ans[i]) for i in range(1, n + 1)))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()