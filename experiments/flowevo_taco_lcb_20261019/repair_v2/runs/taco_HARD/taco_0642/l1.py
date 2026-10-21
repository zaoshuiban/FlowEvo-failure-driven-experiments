import sys

MOD = 1000000007
INV2 = (MOD + 1) // 2


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    ones = 0
    for i in range(1, n + 1):
        if data[i] == b'1':
            ones += 1

    fact_n = 1
    for i in range(2, n + 1):
        fact_n = fact_n * i % MOD

    fact_ones = 1
    for i in range(2, ones + 1):
        fact_ones = fact_ones * i % MOD

    invfact = [1] * (ones + 1)
    invfact[ones] = pow(fact_ones, MOD - 2, MOD)
    for i in range(ones, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    total = 0
    inv_pow2 = 1

    for k in range(ones // 2 + 1):
        term = invfact[k] * invfact[ones - 2 * k] % MOD
        term = term * inv_pow2 % MOD
        total += term
        if total >= MOD:
            total -= MOD
        inv_pow2 = inv_pow2 * INV2 % MOD

    answer = fact_n * total % MOD
    print(answer)


if __name__ == "__main__":
    main()