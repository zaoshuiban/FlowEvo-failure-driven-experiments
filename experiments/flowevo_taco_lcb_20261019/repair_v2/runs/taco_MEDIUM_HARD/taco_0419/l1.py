import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        events_at_end = [[] for _ in range(49)]

        for _ in range(n):
            s = next(it)
            e = next(it)
            c = next(it)
            events_at_end[e].append((s, c))

        dp = [0] * 49

        for end_time in range(49):
            if end_time > 0:
                dp[end_time] = max(dp[end_time], dp[end_time - 1])

            for start_time, compensation in events_at_end[end_time]:
                dp[end_time] = max(
                    dp[end_time],
                    dp[start_time] + compensation
                )

        answers.append(str(dp[48]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()