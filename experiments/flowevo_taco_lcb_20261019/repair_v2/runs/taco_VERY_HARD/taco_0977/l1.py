import sys


def solve_case(N, adj, vals):
    parent = [0] * (N + 1)
    children = [[] for _ in range(N + 1)]
    tin = [0] * (N + 1)
    euler = [0] * N
    order = []

    stack = [1]
    parent[1] = -1

    while stack:
        u = stack.pop()
        tin[u] = len(order)
        euler[len(order)] = u
        order.append(u)

        pu = parent[u]
        for v in adj[u]:
            if v != pu:
                parent[v] = u
                children[u].append(v)
                stack.append(v)

    size = [1] * (N + 1)
    heavy = [0] * (N + 1)

    for u in reversed(order):
        su = 1
        mx = 0
        for v in children[u]:
            sv = size[v]
            su += sv
            if sv > mx:
                mx = sv
                heavy[u] = v
        size[u] = su

    euler_val = [0] * N
    for i in range(N):
        euler_val[i] = vals[euler[i]]

    unique = sorted(set(vals[1:]))
    M = len(unique)
    comp = {v: i for i, v in enumerate(unique)}

    bit = [0] * (M + 1)
    bit_ver = [0] * (M + 1)
    freq = [0] * M
    freq_ver = [0] * M

    current_ver = 1
    active_count = 0
    INF = 10**30
    cur_min = INF
    topbit = 1 << (M.bit_length() - 1)

    def add_value(x):
        nonlocal cur_min, active_count

        pos = comp[x]
        cv = current_ver

        if cur_min:
            if freq_ver[pos] == cv:
                cur_min = 0
            else:
                less = 0
                i = pos
                while i > 0:
                    if bit_ver[i] == cv:
                        less += bit[i]
                    i -= i & -i

                if less:
                    k = less
                    idx = 0
                    mask = topbit

                    while mask:
                        nxt = idx + mask
                        if nxt <= M:
                            if bit_ver[nxt] == cv:
                                val = bit[nxt]
                            else:
                                val = 0

                            if val < k:
                                idx = nxt
                                k -= val
                        mask >>= 1

                    candidate = x ^ unique[idx]
                    if candidate < cur_min:
                        cur_min = candidate

                if active_count > less:
                    k = less + 1
                    idx = 0
                    mask = topbit

                    while mask:
                        nxt = idx + mask
                        if nxt <= M:
                            if bit_ver[nxt] == cv:
                                val = bit[nxt]
                            else:
                                val = 0

                            if val < k:
                                idx = nxt
                                k -= val
                        mask >>= 1

                    candidate = x ^ unique[idx]
                    if candidate < cur_min:
                        cur_min = candidate

        i = pos + 1
        while i <= M:
            if bit_ver[i] != cv:
                bit_ver[i] = cv
                bit[i] = 0
            bit[i] += 1
            i += i & -i

        if freq_ver[pos] != cv:
            freq_ver[pos] = cv
            freq[pos] = 1
        else:
            freq[pos] += 1

        active_count += 1

    ans = [-1] * (N + 1)

    actions = [(0, 1, 1)]

    while actions:
        typ, u, keep = actions.pop()

        if typ == 0:
            actions.append((1, u, keep))

            h = heavy[u]
            if h:
                actions.append((0, h, 1))

            for v in children[u]:
                if v != h:
                    actions.append((0, v, 0))

        else:
            h = heavy[u]

            for v in children[u]:
                if v != h:
                    left = tin[v]
                    right = left + size[v]
                    for idx in range(left, right):
                        add_value(euler_val[idx])

            add_value(vals[u])

            if active_count >= 2:
                ans[u] = cur_min
            else:
                ans[u] = -1

            if not keep:
                current_ver += 1
                active_count = 0
                cur_min = INF

    return ans[1:]


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    output = []

    for _ in range(T):
        N = next(it)

        if N == 1:
            _ = next(it)
            output.append("-1")
            continue

        adj = [[] for _ in range(N + 1)]

        for _ in range(N - 1):
            u = next(it)
            v = next(it)
            adj[u].append(v)
            adj[v].append(u)

        vals = [0] * (N + 1)
        for i in range(1, N + 1):
            vals[i] = next(it)

        ans = solve_case(N, adj, vals)
        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()