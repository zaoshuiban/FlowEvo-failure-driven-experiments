import sys

MOD = 1_000_000_007


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))

    cases = []
    max_freq = 0

    for _ in range(t):
        n = int(next(it))

        max_value = -1
        max_count = 0

        for _ in range(n):
            value = int(next(it))

            if value > max_value:
                max_value = value
                max_count = 1
            elif value == max_value:
                max_count += 1

        cases.append((n, max_count))
        if max_count > max_freq:
            max_freq = max_count

    fact = [1] * (max_freq + 1)
    for i in range(1, max_freq + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (max_freq + 1)
    inv_fact[max_freq] = pow(fact[max_freq], MOD - 2, MOD)

    for i in range(max_freq, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    answers = []

    for n, count_max in cases:
        total = pow(2, n, MOD)

        if count_max & 1:
            answers.append(str(total))
        else:
            half = count_max // 2

            ways_choose_half = (
                fact[count_max]
                * inv_fact[half] % MOD
                * inv_fact[count_max - half] % MOD
            )

            bad = ways_choose_half * pow(2, n - count_max, MOD) % MOD
            answers.append(str((total - bad) % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()