import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    heads = data[2:2 + n]
    targets = data[2 + n:2 + n + m]

    if m == 0:
        print(0)
        return

    def feasible(t: int) -> bool:
        j = 0

        for h in heads:
            if j >= m:
                return True

            p = targets[j]

            # This head cannot reach the first unread target.
            if h + t < p:
                continue

            # No current or later head can reach this target.
            if h - t > p:
                return False

            if p >= h:
                rightmost = h + t
            else:
                rightmost = h

                # Go left to p first, then right.
                reach_left_first = 2 * p + t - h
                if reach_left_first > rightmost:
                    rightmost = reach_left_first

                # Go right first, then left to p.
                reach_right_first = h + (t - (h - p)) // 2
                if reach_right_first > rightmost:
                    rightmost = reach_right_first

            while j < m and targets[j] <= rightmost:
                j += 1

        return j >= m

    lo = -1
    hi = 10**18

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid

    print(hi)


if __name__ == "__main__":
    solve()