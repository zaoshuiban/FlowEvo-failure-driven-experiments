import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    forbidden = [False] * m
    pos = 2
    for _ in range(n):
        forbidden[data[pos]] = True
        pos += 1

    divisors = []
    d = 1
    while d * d <= m:
        if m % d == 0:
            divisors.append(d)
            if d * d != m:
                divisors.append(m // d)
        d += 1
    divisors.sort()

    weight = {d: 0 for d in divisors}
    vertices = {d: [] for d in divisors}

    for x in range(m):
        if not forbidden[x]:
            g = math.gcd(x, m)
            weight[g] += 1
            vertices[g].append(x)

    dp = {}
    parent = {}

    for d in divisors:
        best = 0
        best_parent = None

        for p in divisors:
            if p >= d:
                break
            if d % p == 0 and dp[p] > best:
                best = dp[p]
                best_parent = p

        dp[d] = weight[d] + best
        parent[d] = best_parent if best > 0 else None

    end = divisors[0]
    for d in divisors[1:]:
        if dp[d] > dp[end]:
            end = d

    chain = []
    cur = end
    while cur is not None:
        chain.append(cur)
        cur = parent[cur]
    chain.reverse()

    prefixes = []
    for d in chain:
        if weight[d] > 0:
            prefixes.extend(vertices[d])

    answer = []
    previous_product = None

    for current_product in prefixes:
        if previous_product is None:
            multiplier = current_product % m
        else:
            g = math.gcd(previous_product, m)
            mod = m // g

            if mod == 1:
                multiplier = 0
            else:
                x1 = (previous_product // g) % mod
                y1 = (current_product // g) % mod
                inv = pow(x1, -1, mod)
                multiplier = (y1 * inv) % mod

        answer.append(multiplier)
        previous_product = current_product

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    main()