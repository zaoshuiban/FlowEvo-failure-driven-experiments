import sys
from bisect import bisect_left

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        intervals = []
        for _ in range(n):
            st = data[idx]
            et = data[idx + 1]
            wp = data[idx + 2]
            idx += 3
            intervals.append((st, et, wp))

        intervals.sort(key=lambda x: x[0])
        starts = [x[0] for x in intervals]

        # dp[i] = maximum sum of winning percentages using intervals i..n-1
        dp = [0] * (n + 1)

        for i in range(n - 1, -1, -1):
            st, et, wp = intervals[i]

            # Next interval that starts at or after the current interval ends.
            # Equality is allowed, hence bisect_left.
            j = bisect_left(starts, et, i + 1, n)

            take = wp + dp[j]
            skip = dp[i + 1]
            dp[i] = max(take, skip)

        total = dp[0]
        answers.append(f"{total // 100}.{total % 100:02d}")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()