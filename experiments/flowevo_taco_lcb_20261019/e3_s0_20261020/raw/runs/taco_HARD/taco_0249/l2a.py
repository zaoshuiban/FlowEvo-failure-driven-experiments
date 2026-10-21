import sys
import math


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    forbidden = [False] * m
    for x in data[2:2 + n]:
        forbidden[x] = True

    by_gcd = {}

    for r in range(m):
        if forbidden[r]:
            continue
        g = math.gcd(r, m)  # gcd(0, m) = m
        by_gcd.setdefault(g, []).append(r)

    nodes = sorted(by_gcd.keys())

    exact = {}
    parent = {}
    processed = []

    best_end = -1
    best_value = -1

    for d in nodes:
        weight = len(by_gcd[d])
        best_prev_value = 0
        best_prev_node = -1

        for c in processed:
            if d % c == 0 and exact[c] > best_prev_value:
                best_prev_value = exact[c]
                best_prev_node = c

        exact[d] = weight + best_prev_value
        parent[d] = best_prev_node

        if exact[d] > best_value:
            best_value = exact[d]
            best_end = d

        processed.append(d)

    chain = []
    cur = best_end
    while cur != -1:
        chain.append(cur)
        cur = parent[cur]
    chain.reverse()

    prefix_products = []
    for d in chain:
        prefix_products.extend(by_gcd[d])

    answer = []

    for i, q in enumerate(prefix_products):
        if i == 0:
            answer.append(q % m)
        else:
            p = prefix_products[i - 1]
            g = math.gcd(p, m)
            mod = m // g

            if mod == 1:
                x = 0
            else:
                u = (p // g) % mod
                v = q // g
                inv = pow(u, -1, mod)
                x = (v * inv) % mod

            answer.append(x % m)

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()