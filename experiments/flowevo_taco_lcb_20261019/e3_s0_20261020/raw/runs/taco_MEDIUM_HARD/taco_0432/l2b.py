import sys

MOD = 10**9 + 7

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1

    pow2 = [1]

    def ensure_powers(n):
        while len(pow2) <= n:
            pow2.append((pow2[-1] * 2) % MOD)

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        ensure_powers(n)

        arr.sort()

        total_max = 0
        total_min = 0

        for i, value in enumerate(arr):
            value %= MOD
            total_max = (total_max + value * pow2[i]) % MOD
            total_min = (total_min + value * pow2[n - 1 - i]) % MOD

        answers.append(str((total_max - total_min) % MOD))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()