import sys

MOD = 1_000_000_007
MAXN = 500_000

fact = [1] * (MAXN + 1)
for i in range(1, MAXN + 1):
    fact[i] = fact[i - 1] * i % MOD


def find_centroids(n, adj):
    parent = [0] * (n + 1)
    order = [1]
    parent[1] = -1

    for v in order:
        pv = parent[v]
        for w in adj[v]:
            if w != pv:
                parent[w] = v
                order.append(w)

    sub = [1] * (n + 1)
    for v in reversed(order):
        p = parent[v]
        if p > 0:
            sub[p] += sub[v]

    centroids = []
    for u in range(1, n + 1):
        largest_part = n - sub[u]

        for w in adj[u]:
            if parent[w] == u:
                if sub[w] > largest_part:
                    largest_part = sub[w]

        if largest_part * 2 <= n:
            centroids.append(u)

    return centroids


def calc_C(root, n, adj):
    parent = [0] * (n + 1)
    order = [root]
    parent[root] = -1

    for v in order:
        pv = parent[v]
        for w in adj[v]:
            if w != pv:
                parent[w] = v
                order.append(w)

    sub = [1] * (n + 1)
    prod = 1

    for v in reversed(order):
        sv = sub[v]
        prod = prod * sv % MOD

        p = parent[v]
        if p > 0:
            sub[p] += sv

    c = fact[n] * pow(prod, MOD - 2, MOD) % MOD
    return c, sub


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

        centroids = find_centroids(n, adj)

        if len(centroids) == 2:
            # Equal maximum C values.
            # Descending i tie-break: larger index first.
            if k == 1:
                chosen = max(centroids)
            else:
                chosen = min(centroids)

            c_value, _ = calc_C(chosen, n, adj)
            answers.append(f"{chosen} {c_value}")

        else:
            centroid = centroids[0]

            if k == 1:
                c_value, _ = calc_C(centroid, n, adj)
                answers.append(f"{centroid} {c_value}")

            else:
                c_centroid, sub = calc_C(centroid, n, adj)

                best_node = -1
                best_a = -1

                for v in adj[centroid]:
                    a = sub[v]  # component size on v's side after removing centroid-v

                    if a > best_a or (a == best_a and v > best_node):
                        best_a = a
                        best_node = v

                best_c = c_centroid * best_a % MOD
                best_c = best_c * pow(n - best_a, MOD - 2, MOD) % MOD

                answers.append(f"{best_node} {best_c}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()