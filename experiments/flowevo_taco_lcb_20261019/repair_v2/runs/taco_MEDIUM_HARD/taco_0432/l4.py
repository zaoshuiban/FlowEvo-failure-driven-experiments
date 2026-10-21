import sys

MOD = 1_000_000_007

def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        t = next(data)
    except StopIteration:
        return

    pow2 = [1]
    answers = []

    for _ in range(t):
        n = next(data)
        arr = [next(data) for _ in range(n)]

        while len(pow2) < n:
            pow2.append((pow2[-1] * 2) % MOD)

        arr.sort()

        ans = 0
        for i, value in enumerate(arr):
            coefficient = (pow2[i] - pow2[n - 1 - i]) % MOD
            ans = (ans + (value % MOD) * coefficient) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()