import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    b = data[1 + n:1 + 2 * n]

    base = 0
    positive = []  # a_i > b_i, interval [b_i, a_i]
    negative = []  # a_i < b_i, interval [a_i, b_i]

    for x, y in zip(a, b):
        if x > y:
            base += x - y
            positive.append((y, x))
        elif x < y:
            base += y - x
            negative.append((x, y))

    if not positive or not negative:
        print(base)
        return

    def max_ordered(intervals_a, intervals_b):
        """
        Maximum intersection length between interval A from intervals_a
        and interval B from intervals_b, where B.left <= A.left.
        """
        if not intervals_a or not intervals_b:
            return 0

        intervals_b = sorted(intervals_b)
        intervals_a = sorted(intervals_a)

        j = 0
        max_right_b = -1
        best = 0
        m = len(intervals_b)

        for left_a, right_a in intervals_a:
            while j < m and intervals_b[j][0] <= left_a:
                max_right_b = max(max_right_b, intervals_b[j][1])
                j += 1

            if max_right_b >= left_a:
                intersection = min(right_a, max_right_b) - left_a
                if intersection > best:
                    best = intersection

        return best

    best_gain_interval = max(
        max_ordered(positive, negative),
        max_ordered(negative, positive)
    )

    print(base - 2 * best_gain_interval)


if __name__ == "__main__":
    solve()