import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    a = [0] * (n + 1)
    max_a = 0
    for i in range(1, n + 1):
        a[i] = data[idx]
        idx += 1
        if a[i] > max_a:
            max_a = a[i]

    m = max_a

    buckets = [[] for _ in range(m + 1)]
    for i in range(1, n + 1):
        buckets[a[i]].append(i)

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        x = data[idx]
        y = data[idx + 1]
        idx += 2
        adj[x].append(y)
        adj[y].append(x)

    del data

    # F[d] = number of pairs such that every vertex on the path
    # has value divisible by d.
    F = [0] * (m + 1)
    F[1] = n * (n + 1) // 2

    seen = [0] * (n + 1)

    for d in range(2, m + 1):
        total = 0

        for multiple in range(d, m + 1, d):
            for start in buckets[multiple]:
                if seen[start] == d:
                    continue

                seen[start] = d
                stack = [start]
                size = 0

                while stack:
                    u = stack.pop()
                    size += 1

                    for v in adj[u]:
                        if seen[v] != d and a[v] % d == 0:
                            seen[v] = d
                            stack.append(v)

                total += size * (size + 1) // 2

        F[d] = total

    # Mobius function up to m.
    mu = [0] * (m + 1)
    mu[1] = 1

    primes = []
    composite = [False] * (m + 1)

    for i in range(2, m + 1):
        if not composite[i]:
            primes.append(i)
            mu[i] = -1

        for p in primes:
            ip = i * p
            if ip > m:
                break

            composite[ip] = True

            if i % p == 0:
                mu[ip] = 0
                break
            else:
                mu[ip] = -mu[i]

    # Mobius inversion:
    # ans[d] = sum_{k >= 1} mu[k] * F[d * k]
    for d in range(1, m + 1):
        value = 0
        k = 1

        for multiple in range(d, m + 1, d):
            if mu[k]:
                value += mu[k] * F[multiple]
            k += 1

        F[d] = value

    output = []
    for i in range(1, m + 1):
        if F[i] > 0:
            output.append(f"{i} {F[i]}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()