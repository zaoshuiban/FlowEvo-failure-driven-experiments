import sys


def count_ways(M, N, K):
    if K < M or K > M * N:
        return 0

    dp = [0] * (K + 1)
    dp[0] = 1

    for roll in range(1, M + 1):
        new_dp = [0] * (K + 1)
        window = 0
        max_sum = min(K, roll * N)

        for s in range(1, max_sum + 1):
            window += dp[s - 1]

            remove_idx = s - N - 1
            if remove_idx >= 0:
                window -= dp[remove_idx]

            new_dp[s] = window

        dp = new_dp

    return dp[K]


def format_probability(numerator, denominator):
    if numerator == 0:
        return "0.000 0"

    exponent = 0
    temp = numerator

    while temp < denominator:
        temp *= 10
        exponent += 1

    # mantissa = numerator / denominator * 10^exponent
    scaled_num = numerator * (10 ** (exponent + 3))

    # Round to nearest, ties away from zero (half-up)
    rounded = (2 * scaled_num + denominator) // (2 * denominator)

    if rounded >= 10000:
        rounded = 1000
        exponent -= 1

    integer_part = rounded // 1000
    fractional_part = rounded % 1000

    return f"{integer_part}.{fractional_part:03d} {exponent}"


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        M = int(data[idx])
        N = int(data[idx + 1])
        K = int(data[idx + 2])
        idx += 3

        if K < M or K > M * N:
            answers.append("0.000 0")
            continue

        ways = count_ways(M, N, K)

        if ways == 0:
            answers.append("0.000 0")
            continue

        total = N ** M
        answers.append(format_probability(ways, total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()