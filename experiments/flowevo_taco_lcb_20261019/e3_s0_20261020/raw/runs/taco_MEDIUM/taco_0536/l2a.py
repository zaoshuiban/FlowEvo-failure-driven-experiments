import sys


def format_probability(count, denom):
    if count == 0:
        return "0.000 0"

    num = count
    y = 0

    while num < denom:
        num *= 10
        y += 1

    q, r = divmod(num * 1000, denom)

    # Round to nearest, ties to even (same as standard printf rounding)
    twice = r * 2
    if twice > denom or (twice == denom and (q & 1)):
        q += 1

    if q == 10000:
        q = 1000
        y -= 1

    return f"{q // 1000}.{q % 1000:03d} {y}"


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

        dp = [0] * (K + 1)
        dp[0] = 1

        for i in range(1, M + 1):
            new_dp = [0] * (K + 1)
            window = 0
            max_sum = min(K, i * N)

            for s in range(1, max_sum + 1):
                window += dp[s - 1]

                remove_idx = s - N - 1
                if remove_idx >= 0:
                    window -= dp[remove_idx]

                new_dp[s] = window

            dp = new_dp

        count = dp[K]
        if count == 0:
            answers.append("0.000 0")
        else:
            denom = N ** M
            answers.append(format_probability(count, denom))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()