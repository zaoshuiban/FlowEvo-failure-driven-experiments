import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1

    pow2 = [1]

    def ensure_powers(n):
        while len(pow2) <= n:
            pow2.append((pow2[-1] * 2) % MOD)

    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        arr = data[pos:pos + n]
        pos += n

        ensure_powers(n - 1)
        arr.sort()

        ans = 0

        for i, value in enumerate(arr):
            coefficient = pow2[i] - pow2[n - 1 - i]
            ans = (ans + (value % MOD) * coefficient) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()