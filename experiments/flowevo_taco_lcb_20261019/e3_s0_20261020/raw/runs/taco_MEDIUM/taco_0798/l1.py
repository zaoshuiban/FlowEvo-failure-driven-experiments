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

        matches = []
        for _ in range(n):
            st = data[idx]
            et = data[idx + 1]
            wp = data[idx + 2]
            idx += 3
            matches.append((et, st, wp))

        matches.sort()

        ends = [match[0] for match in matches]
        dp = [0] * (n + 1)

        for i in range(n):
            et, st, wp = matches[i]

            prev = bisect_right(ends, st, 0, i)
            dp[i + 1] = max(dp[i], dp[prev] + wp)

        total = dp[n]
        answers.append(f"{total // 100}.{total % 100:02d}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()