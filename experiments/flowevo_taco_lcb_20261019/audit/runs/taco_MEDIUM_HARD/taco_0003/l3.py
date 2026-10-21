import sys

MOD = 1_000_000_007


def solve():
    data = sys.stdin.buffer.read()

    def int_generator():
        num = 0
        in_number = False
        for c in data:
            if 48 <= c <= 57:
                num = num * 10 + (c - 48)
                in_number = True
            elif in_number:
                yield num
                num = 0
                in_number = False
        if in_number:
            yield num

    it = int_generator()

    try:
        t = next(it)
    except StopIteration:
        return

    tests = []
    max_freq = 0

    for _ in range(t):
        n = next(it)

        max_value = -1
        max_count = 0

        for _ in range(n):
            value = next(it)

            if value > max_value:
                max_value = value
                max_count = 1
            elif value == max_value:
                max_count += 1

        tests.append((n, max_count))
        if max_count > max_freq:
            max_freq = max_count

    fact = [1] * (max_freq + 1)
    for i in range(1, max_freq + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (max_freq + 1)
    invfact[max_freq] = pow(fact[max_freq], MOD - 2, MOD)

    for i in range(max_freq, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    def comb(n, k):
        if k < 0 or k > n:
            return 0
        return fact[n] * invfact[k] % MOD * invfact[n - k] % MOD

    answers = []

    for n, count_max in tests:
        total = pow(2, n, MOD)

        if count_max % 2 == 1:
            answers.append(str(total))
        else:
            half = count_max // 2
            bad = comb(count_max, half) * pow(2, n - count_max, MOD) % MOD
            answers.append(str((total - bad) % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()