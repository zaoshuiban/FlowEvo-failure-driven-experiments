import sys

MOD = 1_000_000_007


def solve() -> None:
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

        # Root the tree at node 1.
        parent = [0] * (n + 1)
        parent[1] = -1
        order = [1]
        pos = 0

        while pos < len(order):
            v = order[pos]
            pos += 1
            pv = parent[v]
            for w in adj[v]:
                if w != pv:
                    parent[w] = v
                    order.append(w)

        # Subtree sizes when rooted at 1.
        sub = [1] * (n + 1)
        for i in range(n - 1, 0, -1):
            v = order[i]
            sub[parent[v]] += sub[v]

        # Find centroid(s).
        half = n // 2
        centroids = []

        for v in range(1, n + 1):
            max_part = n - sub[v]

            for w in adj[v]:
                if parent[w] == v:
                    if sub[w] > max_part:
                        max_part = sub[w]

            if max_part <= half:
                centroids.append(v)

        # Choose the required node.
        if len(centroids) == 2:
            c0, c1 = centroids[0], centroids[1]
            if k == 1:
                u = max(c0, c1)
            else:
                u = min(c0, c1)
        else:
            c = centroids[0]

            if k == 1:
                u = c
            else:
                best_node = -1
                best_size = -1

                for w in adj[c]:
                    if parent[w] == c:
                        size = sub[w]
                    else:
                        size = n - sub[c]

                    if size > best_size or (size == best_size and w > best_node):
                        best_size = size
                        best_node = w

                u = best_node

        # N!
        fact = 1
        for i in range(2, n + 1):
            fact = fact * i % MOD

        # Product of subtree sizes when rooted at node 1.
        product_root1 = 1
        for v in range(1, n + 1):
            product_root1 = product_root1 * sub[v] % MOD

        # Compute product of subtree sizes when rooted at u.
        if u == 1:
            product_u = product_root1
        else:
            numerator = 1
            denominator = 1
            v = u

            while v != 1:
                sv = sub[v]
                numerator = numerator * (n - sv) % MOD
                denominator = denominator * sv % MOD
                v = parent[v]

            product_u = (
                product_root1
                * numerator
                % MOD
                * pow(denominator, MOD - 2, MOD)
                % MOD
            )

        # C_u = N! / product_u
        c_u = fact * pow(product_u, MOD - 2, MOD) % MOD
        answers.append(f"{u} {c_u}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()