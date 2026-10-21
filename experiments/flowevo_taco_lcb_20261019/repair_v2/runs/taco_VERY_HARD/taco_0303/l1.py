import sys

MOD = 1_000_000_007
MAXN = 500_000

fact = [1] * (MAXN + 1)
for i in range(1, MAXN + 1):
    fact[i] = fact[i - 1] * i % MOD


def solve():
    data = sys.stdin.buffer.read()
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

        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            u = next_int() - 1
            v = next_int() - 1
            adj[u].append(v)
            adj[v].append(u)

        if n == 1:
            answers.append("1 1")
            continue

        parent = [-1] * n
        order = [0]

        for v in order:
            for to in adj[v]:
                if to == parent[v]:
                    continue
                parent[to] = v
                order.append(to)

        size = [1] * n

        for v in reversed(order):
            p = parent[v]
            if p != -1:
                size[p] += size[v]

        product_root = 1
        for s in size:
            product_root = product_root * s % MOD

        centroids = []

        for v in range(n):
            mx = n - size[v]

            for to in adj[v]:
                if parent[to] == v:
                    if size[to] > mx:
                        mx = size[to]

            if mx * 2 <= n:
                centroids.append(v)

        fact_n = fact[n]

        def get_value(c):
            num = 1
            den = 1
            v = c

            while parent[v] != -1:
                s = size[v]
                num = num * (n - s) % MOD
                den = den * s % MOD
                v = parent[v]

            denominator = product_root * num % MOD
            return fact_n * den % MOD * pow(denominator, MOD - 2, MOD) % MOD

        if len(centroids) >= 2:
            a, b = centroids[0], centroids[1]
            if a > b:
                a, b = b, a

            chosen = b if k == 1 else a
            value = get_value(chosen)

            answers.append(f"{chosen + 1} {value}")

        else:
            c = centroids[0]
            value_c = get_value(c)

            if k == 1:
                answers.append(f"{c + 1} {value_c}")
            else:
                best_size = -1
                best_node = -1

                for to in adj[c]:
                    if parent[to] == c:
                        component_size = size[to]
                    else:
                        component_size = n - size[c]

                    if component_size > best_size or (
                        component_size == best_size and to > best_node
                    ):
                        best_size = component_size
                        best_node = to

                value = (
                    value_c
                    * best_size
                    % MOD
                    * pow(n - best_size, MOD - 2, MOD)
                    % MOD
                )

                answers.append(f"{best_node + 1} {value}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()