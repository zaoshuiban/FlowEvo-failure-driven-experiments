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

    n = [0] * (N + 1)
    for i in range(1, N + 1):
        n[i] = data[idx]
        idx += 1

    Q = data[idx]
    idx += 1

    queries = data[idx:idx + Q]

    bit = [0] * (B + 2)

    def add(pos, value):
        while pos <= B:
            bit[pos] = (bit[pos] + value) % MOD
            pos += pos & -pos

    def prefix_sum(pos):
        result = 0
        while pos > 0:
            result += bit[pos]
            if result >= MOD:
                result -= MOD
            pos -= pos & -pos
        return result

    dp = [0] * (N + 1)
    dp[B] = 1
    add(B, 1)

    for i in range(B - 1, 0, -1):
        right = i + n[i]
        if right > B:
            right = B

        if right > i:
            ways = prefix_sum(right) - prefix_sum(i)
            ways %= MOD
        else:
            ways = 0

        dp[i] = ways
        if ways:
            add(i, ways)

    answers = [str(dp[s] % MOD) for s in queries]
    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()