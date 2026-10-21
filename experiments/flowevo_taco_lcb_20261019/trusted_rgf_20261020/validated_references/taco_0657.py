import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    idx = 0
    data_len = len(data)

    def next_int():
        nonlocal idx
        while idx < data_len and data[idx] <= 32:
            idx += 1

        sign = 1
        if idx < data_len and data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < data_len and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return num * sign

    t = next_int()
    answers = []
    NEG_INF = -10**30

    for _ in range(t):
        n = next_int()

        # Read first dish and find min/max.
        m = next_int()
        min_first = 10**18
        max_first = -10**18

        for _ in range(m):
            v = next_int()
            if v < min_first:
                min_first = v
            if v > max_first:
                max_first = v

        if n == 1:
            answers.append("0")
            continue

        # Constants for transition from dish 1 with weight 1.
        c1 = -min_first   # max(dp(L) - 1 * L)
        c2 = max_first    # max(dp(L) + 1 * L)

        # Process internal dishes: dish 2 ... dish n-1.
        for j in range(2, n):
            m = next_int()
            arr = [0] * m
            for i in range(m):
                arr[i] = next_int()

            w = j - 1
            w_next = j

            new_c1 = NEG_INF
            new_c2 = NEG_INF

            # Edges (last -> first) in the circular array.
            for i in range(m - 1):
                last = arr[i]
                first = arr[i + 1]

                v1 = c1 + w * first
                v2 = c2 - w * first
                best = v2 if v2 > v1 else v1

                cand1 = best - w_next * last
                cand2 = best + w_next * last

                if cand1 > new_c1:
                    new_c1 = cand1
                if cand2 > new_c2:
                    new_c2 = cand2

            # Last circular edge: arr[-1] -> arr[0]
            last = arr[-1]
            first = arr[0]

            v1 = c1 + w * first
            v2 = c2 - w * first
            best = v2 if v2 > v1 else v1

            cand1 = best - w_next * last
            cand2 = best + w_next * last

            if cand1 > new_c1:
                new_c1 = cand1
            if cand2 > new_c2:
                new_c2 = cand2

            c1, c2 = new_c1, new_c2

        # Read final dish.
        m = next_int()
        min_last = 10**18
        max_last = -10**18

        for _ in range(m):
            v = next_int()
            if v < min_last:
                min_last = v
            if v > max_last:
                max_last = v

        w = n - 1
        ans1 = c1 + w * max_last
        ans2 = c2 - w * min_last
        ans = ans1 if ans1 > ans2 else ans2

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()