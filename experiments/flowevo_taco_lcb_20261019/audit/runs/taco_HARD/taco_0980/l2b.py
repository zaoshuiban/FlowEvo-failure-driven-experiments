import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, m = data[0], data[1]
    heads = data[2:2 + n]
    tracks = data[2 + n:2 + n + m]

    def feasible(t: int) -> bool:
        idx = 0

        for pos in heads:
            if idx == m:
                return True

            target = tracks[idx]

            # This head is too far left to reach the current target.
            if target > pos + t:
                continue

            # This head is too far right, and all following heads are
            # even farther right, so this target can never be read.
            if target < pos - t:
                return False

            if target > pos:
                rightmost = pos + t
            else:
                rightmost = pos

                # Go left first, then right.
                r1 = t - pos + 2 * target
                if r1 > rightmost:
                    rightmost = r1

                # Go right first, then left to target.
                r2 = (t + pos + target) // 2
                if r2 > rightmost:
                    rightmost = r2

            while idx < m and tracks[idx] <= rightmost:
                idx += 1

            if idx == m:
                return True

        return False

    lo, hi = -1, 10**18

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid

    print(hi)


if __name__ == "__main__":
    solve()