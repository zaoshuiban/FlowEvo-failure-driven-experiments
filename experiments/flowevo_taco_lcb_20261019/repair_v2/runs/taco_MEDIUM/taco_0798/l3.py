import sys
from bisect import bisect_right

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
            intervals.append((et, st, wp))

        intervals.sort()
        ends = [interval[0] for interval in intervals]

        dp = [0] * (n + 1)

        for i, (et, st, wp) in enumerate(intervals):
            # Number of already processed matches ending at or before st.
            compatible = bisect_right(ends, st, 0, i)

            take = wp + dp[compatible]
            skip = dp[i]
            dp[i + 1] = max(skip, take)

        total = dp[n]
        answers.append(f"{total // 100}.{total % 100:02d}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()