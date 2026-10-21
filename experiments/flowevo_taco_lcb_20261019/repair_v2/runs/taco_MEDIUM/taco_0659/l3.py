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

        # Time when the first car reaches each flag, using Kahan summation.
        tl = [0.0] * (n + 1)
        comp = 0.0
        prev = 0
        for i in range(1, n + 1):
            x = a[i - 1]
            delta = (x - prev) / i
            y = delta - comp
            s = tl[i - 1] + y
            comp = (s - tl[i - 1]) - y
            tl[i] = s
            prev = x

        # Time when the second car reaches each flag from the right.
        tr = [0.0] * (n + 1)
        comp = 0.0
        prev = l
        for i in range(1, n + 1):
            x = a[n - i]
            delta = (prev - x) / i
            y = delta - comp
            s = tr[i - 1] + y
            comp = (s - tr[i - 1]) - y
            tr[i] = s
            prev = x

        lo = 0.0
        hi = float(l)

        for _ in range(100):
            mid = (lo + hi) * 0.5

            # Position of the first car at time mid.
            k = bisect_right(tl, mid) - 1
            if k == 0:
                start_l = 0.0
            else:
                start_l = float(a[k - 1])
            pos_l = start_l + (k + 1) * (mid - tl[k])

            # Position of the second car at time mid.
            k2 = bisect_right(tr, mid) - 1
            if k2 == 0:
                start_r = float(l)
            else:
                start_r = float(a[n - k2])
            pos_r = start_r - (k2 + 1) * (mid - tr[k2])

            if pos_l >= pos_r:
                hi = mid
            else:
                lo = mid

        answers.append(f"{hi:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()