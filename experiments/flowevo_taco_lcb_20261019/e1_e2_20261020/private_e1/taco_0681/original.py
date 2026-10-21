import sys
import math


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []
    isqrt = math.isqrt

    for _ in range(t):
        n = next_int()
        a = next_int()
        b = next_int()

        events = []
        append = events.append

        for _ in range(n):
            l = next_int()
            r = next_int()
            append((l, 1))
            append((r + 1, -1))

        events.sort()

        k = b - a + 1

        # Maximum possible sum: sum of all numbers from a to b
        total_max = k * b - k * (k - 1) // 2

        p = 2 * a - 1
        c_formula = 2 * b + 1

        current_joy = 0
        prev_time = None
        answer = 0

        i = 0
        m_events = len(events)

        while i < m_events:
            x = events[i][0]

            if prev_time is not None and current_joy > answer:
                left = prev_time
                right = x - 1

                if left <= total_max:
                    # Largest m such that minimum sum of m elements <= right
                    ml = (isqrt(p * p + 8 * right) - p) // 2
                    if ml > k:
                        ml = k

                    # Smallest m such that maximum sum of m elements >= left
                    d = c_formula * c_formula - 8 * left
                    if d >= 0:
                        mh = (c_formula - isqrt(d) + 1) // 2
                        if mh <= ml:
                            answer = current_joy

            delta = 0
            while i < m_events and events[i][0] == x:
                delta += events[i][1]
                i += 1

            current_joy += delta
            prev_time = x

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()