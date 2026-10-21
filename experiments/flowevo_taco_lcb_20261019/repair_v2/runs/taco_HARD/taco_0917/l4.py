import sys

MOD = 1_000_000_007


def main() -> None:
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
    dp = [0] * (N + 1)

    def add(pos: int, value: int) -> None:
        while pos <= B:
            bit[pos] += value
            if bit[pos] >= MOD:
                bit[pos] -= MOD
            pos += pos & -pos

    def prefix_sum(pos: int) -> int:
        result = 0
        while pos > 0:
            result += bit[pos]
            if result >= MOD:
                result -= MOD
            pos -= pos & -pos
        return result

    # dp[i] = number of paths from i to B
    # Empty suffix from B to B counts as 1.
    dp[B] = 1
    add(B, 1)

    for i in range(B - 1, 0, -1):
        right = i + n[i]
        if right > B:
            right = B

        if right > i:
            ways = prefix_sum(right) - prefix_sum(i)
            if ways < 0:
                ways += MOD
        else:
            ways = 0

        dp[i] = ways
        if ways:
            add(i, ways)

    answers = [str(dp[s] % MOD) for s in queries]
    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()