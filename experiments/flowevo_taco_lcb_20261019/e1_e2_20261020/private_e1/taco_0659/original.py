import sys
from bisect import bisect_right


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        l = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        # Time when the first car reaches each flag from the left.
        time_l = [0.0] * n
        s = 0.0
        comp = 0.0
        prev = 0

        for i in range(1, n + 1):
            x = a[i - 1]
            delta = (x - prev) / i
            y = delta - comp
            ns = s + y
            comp = (ns - s) - y
            s = ns
            time_l[i - 1] = s
            prev = x

        # Time when the second car reaches each flag from the right.
        time_r = [0.0] * n
        s = 0.0
        comp = 0.0
        prev = l

        for i in range(1, n + 1):
            x = a[n - i]
            delta = (prev - x) / i
            y = delta - comp
            ns = s + y
            comp = (ns - s) - y
            s = ns
            time_r[i - 1] = s
            prev = x

        lo = 0.0
        hi = float(l)

        for _ in range(100):
            mid = (lo + hi) * 0.5

            k = bisect_right(time_l, mid)
            if k == 0:
                pos_l = mid
            else:
                pos_l = a[k - 1] + (k + 1) * (mid - time_l[k - 1])

            k2 = bisect_right(time_r, mid)
            if k2 == 0:
                pos_r = l - mid
            else:
                pos_r = a[n - k2] - (k2 + 1) * (mid - time_r[k2 - 1])

            if pos_l >= pos_r:
                hi = mid
            else:
                lo = mid

        answers.append(f"{hi:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()