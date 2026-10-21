import sys


def main():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1

        sign = 1
        if data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    T = next_int()
    answers = []

    for _ in range(T):
        N = next_int()
        S = next_int()
        Y = next_int()

        V = [0] * N
        D = [0] * N
        P = [0] * N
        C = [0] * N

        for i in range(N):
            V[i] = next_int()
        for i in range(N):
            D[i] = next_int()
        for i in range(N):
            P[i] = next_int()
        for i in range(N):
            C[i] = next_int()

        # Current time is represented as:
        # base_num / base_den + m * (Y / S)
        base_num = 0
        base_den = 1
        m = 0

        for i in range(N):
            v = V[i]
            d = D[i]
            p = P[i]
            c = C[i]

            # Car blocks x = 0 during [a, b] = [A / v, B / v].
            if d == 1:
                A = -p
                B = c - p
            else:
                A = p
                B = p + c

            # cur = base_num / base_den + m * Y / S
            cur_scaled = base_num * S + m * Y * base_den

            # If cur < b and finish_time >= a, Chef must wait until b.
            if cur_scaled * v < B * base_den * S:
                finish_scaled = base_num * S + (m + 1) * Y * base_den
                if finish_scaled * v >= A * base_den * S:
                    base_num = B
                    base_den = v
                    m = 1
                    continue

            m += 1

        final_num = base_num * S + m * Y * base_den
        final_den = base_den * S
        ans = final_num / final_den

        answers.append(f"{ans:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()