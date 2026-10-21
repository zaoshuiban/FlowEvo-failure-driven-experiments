import sys

def main():
    data = sys.stdin.buffer.read()
    L = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < L and data[idx] <= 32:
            idx += 1

        sign = 1
        if data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < L and data[idx] > 32:
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
        for i in range(N):
            V[i] = next_int()

        D = [0] * N
        for i in range(N):
            D[i] = next_int()

        P = [0] * N
        for i in range(N):
            P[i] = next_int()

        C = [0] * N
        for i in range(N):
            C[i] = next_int()

        # Current time as an exact fraction cur_num / cur_den.
        cur_num = 0
        cur_den = 1

        # Crossing time for one lane = Y / S.
        w_num = Y
        w_den = S

        for i in range(N):
            v = V[i]
            p = P[i]
            c = C[i]

            if D[i] == 1:
                A_num = -p
                B_num = c - p
            else:
                A_num = p
                B_num = p + c

            # Forbidden time interval for x = 0 is [A, B].
            # With the required safety distance 1e-6, Chef must exit before
            # A - 1e-6 / v, or enter after B + 1e-6 / v.
            t1_num = A_num * 1000000 - 1
            t1_den = 1000000 * v

            t2_num = B_num * 1000000 + 1
            t2_den = 1000000 * v

            # cur + w
            plus_num = cur_num * w_den + w_num * cur_den
            plus_den = cur_den * w_den

            # Can Chef cross this lane before the car arrives?
            if plus_num * t1_den < t1_num * plus_den:
                cur_num = plus_num
                cur_den = plus_den
            else:
                # If the car has already passed, cross immediately.
                if cur_num * t2_den >= t2_num * cur_den:
                    cur_num = plus_num
                    cur_den = plus_den
                else:
                    # Wait until the car has completely passed.
                    cur_num = t2_num * w_den + w_num * t2_den
                    cur_den = t2_den * w_den

        answers.append(f"{cur_num / cur_den:.10f}\n")

    sys.stdout.write("".join(answers))


if __name__ == "__main__":
    main()