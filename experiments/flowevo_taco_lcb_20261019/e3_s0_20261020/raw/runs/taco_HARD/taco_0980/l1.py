import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    heads = [next(it) for _ in range(n)]
    tracks = [next(it) for _ in range(m)]

    def can_read(time_limit: int) -> bool:
        j = 0

        for h in heads:
            if j >= m:
                return True

            cur = tracks[j]

            if cur < h - time_limit:
                return False

            if cur > h + time_limit:
                continue

            if cur >= h:
                rightmost = h + time_limit
            else:
                # Visit cur first, then go right:
                reach1 = time_limit - h + 2 * cur

                # Go right first, then visit cur:
                reach2 = (time_limit + h + cur) // 2

                rightmost = reach1 if reach1 > reach2 else reach2

                if rightmost < h:
                    rightmost = h

            while j < m and tracks[j] <= rightmost:
                j += 1

        return j >= m

    low = -1
    high = 10**18

    while high - low > 1:
        mid = (low + high) // 2
        if can_read(mid):
            high = mid
        else:
            low = mid

    print(high)


if __name__ == "__main__":
    solve()