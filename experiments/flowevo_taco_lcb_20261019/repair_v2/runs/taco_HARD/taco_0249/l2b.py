import sys
import math


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    forbidden_values = data[2:2 + n]

    if m == 1:
        # n must be 0. The only valid non-empty sequence has one prefix product: 0.
        sys.stdout.write("1\n0\n")
        return

    forbidden = [False] * m
    for v in forbidden_values:
        forbidden[v] = True

    # class_res[d] = allowed residues x, 1 <= x < m, such that gcd(x, m) = d
    class_res = {}

    for x in range(1, m):
        if not forbidden[x]:
            d = math.gcd(x, m)
            class_res.setdefault(d, []).append(x)

    zero_allowed = not forbidden[0]

    keys = sorted(class_res.keys())
    dp = {}
    prev = {}

    best_d = None
    best_value = -1

    # Longest weighted chain in the divisor poset of gcd classes.
    for d in keys:
        best_before = 0
        best_prev = None

        for e, val in dp.items():
            if d % e == 0 and val > best_before:
                best_before = val
                best_prev = e

        current_value = best_before + len(class_res[d])
        dp[d] = current_value
        prev[d] = best_prev

        if current_value > best_value:
            best_value = current_value
            best_d = d

    prefix_products = []

    if best_d is not None:
        chain = []
        cur = best_d

        while cur is not None:
            chain.append(cur)
            cur = prev.get(cur)

        chain.reverse()

        for d in chain:
            prefix_products.extend(class_res[d])

    if zero_allowed:
        prefix_products.append(0)

    k = len(prefix_products)
    answer = []

    if k > 0:
        # First element must create the first desired prefix product.
        answer.append(prefix_products[0] % m)

        for i in range(1, k):
            x = prefix_products[i - 1]
            y = prefix_products[i]

            d = math.gcd(x, m)
            mod = m // d

            if mod == 1:
                a = 0
            else:
                x_reduced = (x // d) % mod
                y_reduced = (y // d) % mod
                inv = pow(x_reduced, -1, mod)
                a = (y_reduced * inv) % mod

            answer.append(a)

    sys.stdout.write(str(k) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()