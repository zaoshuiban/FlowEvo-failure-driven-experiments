import sys
import bisect


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        intervals = []

        for _ in range(n):
            start = next(it)
            end = next(it)
            win_percent = next(it)
            intervals.append((end, start, win_percent))

        intervals.sort()
        ends = [interval[0] for interval in intervals]

        dp = [0] * (n + 1)

        for i, (end, start, win_percent) in enumerate(intervals, start=1):
            j = bisect.bisect_right(ends, start, 0, i - 1)
            take = dp[j] + win_percent
            skip = dp[i - 1]
            dp[i] = max(skip, take)

        answers.append(f"{dp[n] / 100:.2f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()