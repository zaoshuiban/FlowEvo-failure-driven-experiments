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

        pos2 = [[] for _ in range(26)]
        for j, ch in enumerate(s2):
            pos2[ch - 65].append(j)

        N = n - 1
        M = m - 1
        D = N - M

        ans = INF

        for p, ch in enumerate(s1):
            q_positions = pos2[ch - 65]
            if not q_positions:
                continue

            # For fixed p, ugliness as a function of q is:
            # |q-(N-p)| + |q-(M-p)| + |q-p| + |q-(p-D)|
            # It is minimized on the median interval of these four points.
            values = [N - p, M - p, p, p - D]
            values.sort()

            median_left = values[1]

            k = bisect_left(q_positions, median_left)

            if k < len(q_positions):
                q = q_positions[k]
                val = (
                    abs(p - q)
                    + abs(p + q - N)
                    + abs(p - q - D)
                    + abs(p + q - M)
                )
                if val < ans:
                    ans = val

            if k > 0:
                q = q_positions[k - 1]
                val = (
                    abs(p - q)
                    + abs(p + q - N)
                    + abs(p - q - D)
                    + abs(p + q - M)
                )
                if val < ans:
                    ans = val

            if ans == 0:
                break

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()