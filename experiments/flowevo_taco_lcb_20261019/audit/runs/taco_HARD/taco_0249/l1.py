import sys
from math import gcd


def solve_congruence(a, b, mod):
    """
    Returns x such that a * x == b (mod mod).
    It is guaranteed that a solution exists.
    """
    g = gcd(a, mod)
    m1 = mod // g

    if m1 == 1:
        return 0

    a1 = (a // g) % m1
    b1 = (b // g) % m1

    inv = pow(a1, -1, m1)
    return (b1 * inv) % m1


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    forbidden = bytearray(m)
    for x in data[2:2 + n]:
        forbidden[x] = 1

    # residues[d] = allowed residues x with gcd(x, m) = d
    residues = {}

    for x in range(m):
        if not forbidden[x]:
            d = gcd(x, m)
            residues.setdefault(d, []).append(x)

    keys = sorted(residues.keys())

    # Find the maximum-weight chain of gcd classes under divisibility.
    dp = {}
    parent = {}
    best_end = None
    best_value = -1

    for d in keys:
        best_prev_value = 0
        best_prev = None

        for e in keys:
            if e >= d:
                break
            if d % e == 0 and dp[e] > best_prev_value:
                best_prev_value = dp[e]
                best_prev = e

        value = best_prev_value + len(residues[d])
        dp[d] = value
        parent[d] = best_prev

        if value > best_value:
            best_value = value
            best_end = d

    chain = []
    d = best_end
    while d is not None:
        chain.append(d)
        d = parent[d]
    chain.reverse()

    # Desired prefix products.
    prefix_products = []
    for d in chain:
        prefix_products.extend(residues[d])

    # Convert desired prefix products into the actual sequence elements.
    answer = []
    if prefix_products:
        answer.append(prefix_products[0] % m)

        for i in range(1, len(prefix_products)):
            prev_p = prefix_products[i - 1]
            cur_p = prefix_products[i]
            answer.append(solve_congruence(prev_p, cur_p, m))

    k = len(answer)
    sys.stdout.write(str(k) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    main()