import sys


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
    output = []

    for _ in range(t):
        n = next_int()

        if n == 1:
            next_int()  # P[0], always 1
            a = next_int()
            b = next_int()
            output.append("1" if a >= b else "-1")
            continue

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        P = [0] * n
        pos = [0] * (n + 1)
        for i in range(n):
            x = next_int()
            P[i] = x
            pos[x] = i + 1

        A = [0] * (n + 1)
        for i in range(1, n + 1):
            A[i] = next_int()

        B = [0] * (n + 1)
        for i in range(1, n + 1):
            B[i] = next_int()

        # Build the elimination tree.
        parent = [0] * (n + 1)
        dsu = list(range(n + 1))
        size = [0] * (n + 1)
        top = [0] * (n + 1)
        active = bytearray(n + 1)

        def find(x):
            while dsu[x] != x:
                dsu[x] = dsu[dsu[x]]
                x = dsu[x]
            return x

        for i in range(n - 1, -1, -1):
            x = P[i]
            active[x] = 1
            dsu[x] = x
            size[x] = 1
            top[x] = x

            for y in adj[x]:
                if not active[y]:
                    continue

                rx = find(x)
                ry = find(y)
                if rx == ry:
                    continue

                parent[top[ry]] = x

                if size[rx] < size[ry]:
                    dsu[rx] = ry
                    size[ry] += size[rx]
                    top[ry] = x
                else:
                    dsu[ry] = rx
                    size[rx] += size[ry]
                    top[rx] = x

        # Prefix sums of A on the elimination tree.
        prefix_sum = [0] * (n + 1)
        for x in P:
            p = parent[x]
            if p:
                prefix_sum[x] = prefix_sum[p] + A[x]
            else:
                prefix_sum[x] = A[x]

        LOG = max(1, n.bit_length())
        up = [parent]

        for _ in range(1, LOG):
            prev = up[-1]
            cur = [prev[prev[v]] for v in range(n + 1)]
            up.append(cur)

        answer = [0] * (n + 1)

        for v in range(1, n + 1):
            needed = B[v]

            if prefix_sum[v] < needed:
                answer[v] = -1
                continue

            cur = v

            for k in range(LOG - 1, -1, -1):
                anc = up[k][cur]
                if anc and prefix_sum[anc] >= needed:
                    cur = anc

            answer[v] = pos[cur]

        output.append(" ".join(str(answer[i]) for i in range(1, n + 1)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()