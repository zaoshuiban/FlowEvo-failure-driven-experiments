import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    heads = data[2:2 + n]
    tracks = data[2 + n:2 + n + m]

    if m == 0:
        print(0)
        return

    def feasible(t: int) -> bool:
        j = 0

        for h in heads:
            if j == m:
                return True

            p = tracks[j]

            # This head cannot reach the leftmost unread track.
            if h + t < p:
                continue

            # All following heads are to the right, so nobody can reach it.
            if h - t > p:
                return False

            if p >= h:
                rightmost = h + t
            else:
                rightmost = h

                # Go right first, then left to p.
                v = (h + t + p) // 2
                if v > rightmost:
                    rightmost = v

                # Go left to p first, then right.
                v = h + t - 2 * (h - p)
                if v > rightmost:
                    rightmost = v

            while j < m and tracks[j] <= rightmost:
                j += 1

        return j == m

    max_coord = max(heads[-1], tracks[-1])
    min_coord = min(heads[0], tracks[0])

    lo = -1
    hi = 2 * (max_coord - min_coord) + 1

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid

    print(hi)


if __name__ == "__main__":
    solve()