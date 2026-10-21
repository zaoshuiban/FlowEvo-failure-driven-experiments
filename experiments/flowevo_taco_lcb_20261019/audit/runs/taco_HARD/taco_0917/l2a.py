import sys

MOD = 1000000007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    N = data[idx]
    idx += 1
    B = data[idx]
    idx += 1

    nxt = [0] * (N + 1)
    for i in range(1, N + 1):
        nxt[i] = data[idx]
        idx += 1

    Q = data[idx]
    idx += 1

    queries = data[idx:idx + Q]

    dp = [0] * (N + 1)
    suffix = [0] * (N + 2)

    for i in range(N, 0, -1):
        if i == B:
            dp[i] = 1
        else:
            right = i + nxt[i]
            if right > N:
                right = N
            dp[i] = (suffix[i + 1] - suffix[right + 1]) % MOD

        suffix[i] = (suffix[i + 1] + dp[i]) % MOD

    answers = [str(dp[s] % MOD) for s in queries]
    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()