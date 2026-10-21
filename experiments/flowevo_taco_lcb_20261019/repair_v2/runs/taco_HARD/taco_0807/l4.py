import sys
from bisect import bisect_left


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []
    INF = 10**18

    for _ in range(t):
        s1 = data[idx]
        s2 = data[idx + 1]
        idx += 2

        n = len(s1)
        m = len(s2)

        positions = [[] for _ in range(26)]
        for j, ch in enumerate(s2):
            positions[ch - 65].append(j)

        N = n - 1
        M = m - 1
        ans = INF

        for p, ch in enumerate(s1):
            q_positions = positions[ch - 65]
            if not q_positions:
                continue

            # For fixed p, ugliness as a function of q is:
            # |q - p| + |q - (M-p)| + |q - (N-p)| + |q - (p-N+M)|
            # Its minimum over q_positions is around the lower median.
            centers = [p, M - p, N - p, p - N + M]
            centers.sort()
            median = centers[1]

            k = bisect_left(q_positions, median)

            if k < len(q_positions):
                q = q_positions[k]
                value = (
                    abs(p - q)
                    + abs(p - (M - q))
                    + abs((N - p) - q)
                    + abs((N - p) - (M - q))
                )
                if value < ans:
                    ans = value

            if k > 0:
                q = q_positions[k - 1]
                value = (
                    abs(p - q)
                    + abs(p - (M - q))
                    + abs((N - p) - q)
                    + abs((N - p) - (M - q))
                )
                if value < ans:
                    ans = value

            if ans == 0:
                break

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()