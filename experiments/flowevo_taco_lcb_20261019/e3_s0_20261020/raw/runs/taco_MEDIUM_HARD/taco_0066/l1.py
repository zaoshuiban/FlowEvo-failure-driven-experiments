import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    speeds = sorted(data[1:1 + n])

    # prev[l] stores the minimum sum of discrepancies for the interval
    # speeds[l ... l + length - 1], where 'length' is the current length.
    prev = [0] * n

    for length in range(2, n + 1):
        count = n - length + 1
        cur = [0] * count

        for left in range(count):
            right = left + length - 1
            best_previous = prev[left]
            if prev[left + 1] < best_previous:
                best_previous = prev[left + 1]

            cur[left] = best_previous + (speeds[right] - speeds[left])

        prev = cur

    print(prev[0])


if __name__ == "__main__":
    solve()