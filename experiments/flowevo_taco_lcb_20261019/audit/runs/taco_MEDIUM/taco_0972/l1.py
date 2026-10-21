import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    sources = []
    pos = 3
    for _ in range(k):
        x, y = data[pos], data[pos + 1]
        pos += 2
        sources.append((x, y))

    def covered(radius):
        for row in range(1, n + 1):
            intervals = []

            for sx, sy in sources:
                rem = radius - abs(row - sx)
                if rem >= 0:
                    left = max(1, sy - rem)
                    right = min(m, sy + rem)
                    if left <= right:
                        intervals.append((left, right))

            if not intervals:
                return False

            intervals.sort()

            reach = 0
            for left, right in intervals:
                if left > reach + 1:
                    return False
                if right > reach:
                    reach = right
                if reach >= m:
                    break

            if reach < m:
                return False

        return True

    low = -1
    high = n + m

    while high - low > 1:
        mid = (low + high) // 2
        if covered(mid):
            high = mid
        else:
            low = mid

    max_dist = high

    if max_dist == 0:
        print(1, 1)
        return

    radius = max_dist - 1

    for row in range(1, n + 1):
        intervals = []

        for sx, sy in sources:
            rem = radius - abs(row - sx)
            if rem >= 0:
                left = max(1, sy - rem)
                right = min(m, sy + rem)
                if left <= right:
                    intervals.append((left, right))

        intervals.sort()

        reach = 0
        answer_y = 0

        for left, right in intervals:
            if left > reach + 1:
                answer_y = reach + 1
                break
            if right > reach:
                reach = right
            if reach >= m:
                break

        if answer_y == 0 and reach < m:
            answer_y = reach + 1

        if answer_y != 0:
            print(row, answer_y)
            return


if __name__ == "__main__":
    main()