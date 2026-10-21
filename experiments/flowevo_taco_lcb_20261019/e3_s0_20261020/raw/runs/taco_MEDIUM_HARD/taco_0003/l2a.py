import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    tests = []
    max_n = 0

    for _ in range(t):
        n = data[idx]
        idx += 1

        max_val = -1
        freq = 0

        for j in range(idx, idx + n):
            v = data[j]
            if v > max_val:
                max_val = v
                freq = 1
            elif v == max_val:
                freq += 1

        idx += n
        tests.append((n, freq))
        if n > max_n:
            max_n = n

    del data

    fact = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (max_n + 1)
    inv_fact[max_n] = pow(fact[max_n], MOD - 2, MOD)
    for i in range(max_n, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    def comb(n, k):
        if k < 0 or k > n:
            return 0
        return fact[n] * inv_fact[k] % MOD * inv_fact[n - k] % MOD

    answers = []

    for n, freq in tests:
        ans = pow(2, n, MOD)

        if freq % 2 == 0:
            half = freq // 2
            excluded = comb(freq, half) * pow(2, n - freq, MOD) % MOD
            ans = (ans - excluded) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()