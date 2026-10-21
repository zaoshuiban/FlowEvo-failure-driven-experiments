import sys

MOD = 1_000_000_007
MAXN = 500_000

fact = [1] * (MAXN + 1)
for i in range(1, MAXN + 1):
    fact[i] = fact[i - 1] * i % MOD


def solve():
    data = sys.stdin.buffer.read()
    if not data:
        return

    pos = 0
    length = len(data)

    def next_int():
        nonlocal pos
        while pos < length and data[pos] <= 32:
            pos += 1
        num = 0
        while pos < length and data[pos] > 32:
            num = num * 10 + (data[pos] - 48)
            pos += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        k = next_int()

        adj = [[] for _ in range(n + 1)]

        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        if n == 1:
            answers.append("1 1")
            continue

        parent = [0] * (n + 1)
        order = [1]
        idx = 0

        while idx < len(order):
            u = order[idx]
            idx += 1
            pu = parent[u]

            for v in adj[u]:
                if v != pu:
                    parent[v] = u
                    order.append(v)

        size = [1] * (n + 1)

        for u in reversed(order):
            p = parent[u]
            if p:
                size[p] += size[u]

        centroids = []

        for u in range(1, n + 1):
            max_part = n - size[u]

            for v in adj[u]:
                if parent[v] == u and size[v] > max_part:
                    max_part = size[v]

            if max_part * 2 <= n:
                centroids.append(u)

        if len(centroids) >= 2:
            c1, c2 = centroids[0], centroids[1]

            if k == 1:
                chosen = c1 if c1 > c2 else c2
            else:
                chosen = c1 if c1 < c2 else c2

            parent = [0] * (n + 1)
            order = [chosen]
            idx = 0

            while idx < len(order):
                u = order[idx]
                idx += 1
                pu = parent[u]

                for v in adj[u]:
                    if v != pu:
                        parent[v] = u
                        order.append(v)

            size = [1] * (n + 1)
            product = 1

            for u in reversed(order):
                product = product * size[u] % MOD
                p = parent[u]
                if p:
                    size[p] += size[u]

            c_value = fact[n] * pow(product, MOD - 2, MOD) % MOD
            answers.append(f"{chosen} {c_value}")

        else:
            c = centroids[0]

            parent = [0] * (n + 1)
            order = [c]
            idx = 0

            while idx < len(order):
                u = order[idx]
                idx += 1
                pu = parent[u]

                for v in adj[u]:
                    if v != pu:
                        parent[v] = u
                        order.append(v)

            size = [1] * (n + 1)
            product = 1

            for u in reversed(order):
                product = product * size[u] % MOD
                p = parent[u]
                if p:
                    size[p] += size[u]

            centroid_value = fact[n] * pow(product, MOD - 2, MOD) % MOD

            if k == 1:
                answers.append(f"{c} {centroid_value}")
            else:
                best_node = -1
                best_size = -1

                for v in adj[c]:
                    s = size[v]
                    if s > best_size or (s == best_size and v > best_node):
                        best_size = s
                        best_node = v

                selected_value = (
                    centroid_value
                    * best_size
                    % MOD
                    * pow(n - best_size, MOD - 2, MOD)
                    % MOD
                )

                answers.append(f"{best_node} {selected_value}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()