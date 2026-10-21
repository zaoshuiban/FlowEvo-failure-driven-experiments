import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]

    # Find maximum N to precompute factorials.
    pos = 1
    max_n = 0
    for _ in range(t):
        n = data[pos]
        pos += 1
        if n > max_n:
            max_n = n
        pos += n

    fact = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (max_n + 1)
    inv_fact[max_n] = pow(fact[max_n], MOD - 2, MOD)
    for i in range(max_n, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    pow2 = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        pow2[i] = pow2[i - 1] * 2 % MOD

    def comb(n, k):
        if k < 0 or k > n:
            return 0
        return fact[n] * inv_fact[k] % MOD * inv_fact[n - k] % MOD

    answers = []
    pos = 1

    for _ in range(t):
        n = data[pos]
        pos += 1

        end = pos + n
        maximum = -1
        count_max = 0

        for i in range(pos, end):
            value = data[i]
            if value > maximum:
                maximum = value
                count_max = 1
            elif value == maximum:
                count_max += 1

        pos = end

        total = pow2[n]

        if count_max % 2 == 0:
            draw_ways = comb(count_max, count_max // 2) * pow2[n - count_max] % MOD
            total = (total - draw_ways) % MOD

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()