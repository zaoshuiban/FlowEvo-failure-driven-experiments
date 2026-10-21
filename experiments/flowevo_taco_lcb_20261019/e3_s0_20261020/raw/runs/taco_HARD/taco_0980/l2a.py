import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    heads = data[2:2 + n]
    targets = data[2 + n:2 + n + m]

    def can(time: int) -> bool:
        j = 0

        for h in heads:
            if j >= m:
                return True

            x = targets[j]

            if h + time < x:
                continue

            if h - time > x:
                return False

            if h <= x:
                rightmost = h + time
            else:
                # Go left to x first, then right.
                r1 = time - h + 2 * x
                # Go right first, then left to x.
                r2 = (time + h + x) // 2
                rightmost = max(h, r1, r2)

            while j < m and targets[j] <= rightmost:
                j += 1

        return j >= m

    low = 0
    high = 10**18

    while low < high:
        mid = (low + high) // 2
        if can(mid):
            high = mid
        else:
            low = mid + 1

    print(low)


if __name__ == "__main__":
    solve()