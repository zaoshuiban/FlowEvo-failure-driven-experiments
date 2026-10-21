import sys
import math


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    n_data = len(data)

    def next_int():
        nonlocal idx
        while idx < n_data and data[idx] <= 32:
            idx += 1

        sign = 1
        if data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < n_data and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    t = next_int()
    answers = []
    gcd = math.gcd

    for _ in range(t):
        n = next_int()
        s = next_int()
        y = next_int()

        v = [0] * n
        for i in range(n):
            v[i] = next_int()

        direction = [0] * n
        for i in range(n):
            direction[i] = next_int()

        p = [0] * n
        for i in range(n):
            p[i] = next_int()

        c = [0] * n
        for i in range(n):
            c[i] = next_int()

        # Common denominator for all times in this test case.
        den = s
        for speed in v:
            g = gcd(den, speed)
            den = den // g * speed

        cross_time = y * (den // s)
        current = 0

        for i in range(n):
            speed = v[i]
            factor = den // speed

            if direction[i] == 1:
                left = (-p[i]) * factor
                right = (c[i] - p[i]) * factor
            else:
                left = p[i] * factor
                right = (c[i] + p[i]) * factor

            if current + cross_time < left:
                current += cross_time
            elif current >= right:
                current += cross_time
            else:
                current = right + cross_time

        ans = current / den
        answers.append(f"{ans:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()