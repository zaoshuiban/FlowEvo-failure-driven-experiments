import sys
import math

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    g = 0
    for x in a:
        g = math.gcd(g, x)

    if g != 1:
        print(-1)
        return

    m = max(a)

    freq = [0] * (m + 1)
    for x in a:
        freq[x] += 1

    # cnt[d] = number of elements divisible by d
    cnt = [0] * (m + 1)
    for d in range(1, m + 1):
        s = 0
        for multiple in range(d, m + 1, d):
            s += freq[multiple]
        cnt[d] = s

    # Möbius function up to m
    mu = [0] * (m + 1)
    mu[1] = 1
    primes = []
    is_composite = [False] * (m + 1)

    for i in range(2, m + 1):
        if not is_composite[i]:
            primes.append(i)
            mu[i] = -1

        for p in primes:
            v = i * p
            if v > m:
                break

            is_composite[v] = True

            if i % p == 0:
                mu[v] = 0
                break
            else:
                mu[v] = -mu[i]

    totals = [0] * 8

    for d in range(1, m + 1):
        md = mu[d]
        if md == 0:
            continue

        c = cnt[d]
        if c == 0:
            continue

        comb = 1
        limit = min(7, c)

        for k in range(1, limit + 1):
            comb = comb * (c - k + 1) // k
            totals[k] += md * comb

    for k in range(1, 8):
        if totals[k] > 0:
            print(k)
            return

    print(-1)


if __name__ == "__main__":
    solve()