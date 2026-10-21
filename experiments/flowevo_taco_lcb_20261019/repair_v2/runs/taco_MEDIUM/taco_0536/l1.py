import sys


def count_ways(m, n, k):
    if k < m or k > m * n:
        return 0

    dp = [0] * (k + 1)
    dp[0] = 1

    for _ in range(m):
        ndp = [0] * (k + 1)
        window = 0

        for s in range(1, k + 1):
            window += dp[s - 1]

            if s - n - 1 >= 0:
                window -= dp[s - n - 1]

            ndp[s] = window

        dp = ndp

    return dp[k]


def format_probability(ways, total):
    if ways == 0:
        return "0.000 0"

    y = 0
    num = ways

    while num < total:
        num *= 10
        y += 1

    # Round (num / total) * 1000 to the nearest integer, half up.
    scaled = (2 * num * 1000 + total) // (2 * total)

    # Handle cases like 9.9996 -> 10.000 -> 1.000 * 10^(y-1)
    if scaled == 10000:
        scaled = 1000
        y -= 1

    integer_part = scaled // 1000
    fractional_part = scaled % 1000

    return f"{integer_part}.{fractional_part:03d} {y}"


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        m = data[idx]
        n = data[idx + 1]
        k = data[idx + 2]
        idx += 3

        if k < m or k > m * n:
            answers.append("0.000 0")
            continue

        ways = count_ways(m, n, k)
        total = n ** m

        answers.append(format_probability(ways, total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()