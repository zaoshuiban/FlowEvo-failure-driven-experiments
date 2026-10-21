import sys
import math

def main():
    data = sys.stdin.buffer.read().split()
    a = int(data[0])
    n = int(data[1])
    b = a + n - 1

    limit = math.isqrt(b)

    mu = [0] * (limit + 1)
    mu[1] = 1
    primes = []
    composite = [False] * (limit + 1)

    for i in range(2, limit + 1):
        if not composite[i]:
            primes.append(i)
            mu[i] = -1

        for p in primes:
            v = i * p
            if v > limit:
                break

            composite[v] = True

            if i % p == 0:
                mu[v] = 0
                break
            else:
                mu[v] = -mu[i]

    terms = []
    for d in range(1, limit + 1):
        if mu[d] != 0:
            terms.append((d * d, mu[d]))

    def squarefree_sum(x):
        if x <= 0:
            return 0

        result = 0
        for dd, m in terms:
            if dd > x:
                break

            t = x // dd
            result += m * dd * (t * (t + 1) // 2)

        return result

    answer = 0
    q = 1

    while q * q <= b:
        q2 = q * q

        left = (a + q2 - 1) // q2
        right = b // q2

        if left <= right:
            answer += squarefree_sum(right) - squarefree_sum(left - 1)

        q += 1

    print(answer)


if __name__ == "__main__":
    main()