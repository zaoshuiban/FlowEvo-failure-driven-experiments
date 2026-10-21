import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    pow2 = [1]
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        while len(pow2) <= n:
            pow2.append((pow2[-1] * 2) % MOD)

        arr.sort()

        ans = 0
        for i, value in enumerate(arr):
            ans = (ans + value * (pow2[i] - pow2[n - 1 - i])) % MOD

        answers.append(str(ans % MOD))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()