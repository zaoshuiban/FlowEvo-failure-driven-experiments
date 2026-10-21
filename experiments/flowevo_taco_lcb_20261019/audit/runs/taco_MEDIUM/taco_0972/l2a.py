import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    k = data[2]

    sources = []
    idx = 3
    for _ in range(k):
        x, y = data[idx], data[idx + 1]
        idx += 2
        sources.append((x, y))

    def find_uncovered(radius):
        for x in range(1, n + 1):
            intervals = []

            for sx, sy in sources:
                dx = abs(x - sx)
                rem = radius - dx

                if rem >= 0:
                    left = sy - rem
                    right = sy + rem

                    if left < 1:
                        left = 1
                    if right > m:
                        right = m

                    if left <= right:
                        intervals.append((left, right))

            if not intervals:
                return x, 1

            intervals.sort()

            cur = 1
            for left, right in intervals:
                if left > cur:
                    return x, cur

                if right >= cur:
                    cur = right + 1
                    if cur > m:
                        break

            if cur <= m:
                return x, cur

        return None

    low, high = 0, n + m

    while low < high:
        mid = (low + high) // 2

        if find_uncovered(mid) is None:
            high = mid
        else:
            low = mid + 1

    answer_radius = low

    if answer_radius == 0:
        print(sources[0][0], sources[0][1])
    else:
        x, y = find_uncovered(answer_radius - 1)
        print(x, y)


if __name__ == "__main__":
    main()