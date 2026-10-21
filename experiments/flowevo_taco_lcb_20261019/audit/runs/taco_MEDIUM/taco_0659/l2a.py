import sys
from bisect import bisect_right


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        l = int(data[idx + 1])
        idx += 2

        a = [int(data[idx + i]) for i in range(n)]
        idx += n

        # Time moments when the left car reaches each flag
        left_time = [0.0] * (n + 1)
        prev = 0.0
        for i in range(1, n + 1):
            x = a[i - 1]
            left_time[i] = left_time[i - 1] + (x - prev) / i
            prev = x

        # Time moments when the right car reaches each flag
        right_time = [0.0] * (n + 1)
        prev = float(l)
        for i in range(1, n + 1):
            x = a[n - i]
            right_time[i] = right_time[i - 1] + (prev - x) / i
            prev = x

        def can_meet(time):
            i = bisect_right(left_time, time) - 1
            left_last = a[i - 1] if i > 0 else 0.0
            left_pos = left_last + (time - left_time[i]) * (i + 1)

            j = bisect_right(right_time, time) - 1
            right_last = a[n - j] if j > 0 else l
            right_pos = right_last - (time - right_time[j]) * (j + 1)

            return left_pos >= right_pos

        lo, hi = 0.0, float(l)

        for _ in range(100):
            mid = (lo + hi) / 2.0
            if can_meet(mid):
                hi = mid
            else:
                lo = mid

        answers.append(f"{hi:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()