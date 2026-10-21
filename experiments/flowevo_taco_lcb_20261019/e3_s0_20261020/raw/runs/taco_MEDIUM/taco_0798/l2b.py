import sys
import bisect

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
            start = data[idx]
            end = data[idx + 1]
            wp = data[idx + 2]
            idx += 3
            intervals.append((end, start, wp))

        intervals.sort()
        ends = [interval[0] for interval in intervals]

        dp = [0] * (n + 1)

        for i, (end, start, wp) in enumerate(intervals):
            compatible = bisect.bisect_right(ends, start, 0, i + 1)
            take = wp + dp[compatible]
            skip = dp[i]
            dp[i + 1] = max(skip, take)

        answers.append(f"{dp[n] / 100:.2f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()