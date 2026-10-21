import sys
from bisect import bisect_left, bisect_right


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    in_number = False
    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_number = True
        elif in_number:
            yield num
            num = 0
            in_number = False
    if in_number:
        yield num


def solve():
    it = iter(int_generator())
    try:
        T = next(it)
    except StopIteration:
        return

    answers = []
    NEG = -10**100

    for _ in range(T):
        N = next(it)

        M = next(it)
        first_dish = [next(it) for _ in range(M)]

        if N == 1:
            answers.append("0")
            continue

        prev_vals = sorted(set(first_dish))
        prev_best = [0] * len(prev_vals)

        ans = 0

        for dish_idx in range(2, N + 1):
            M = next(it)
            arr = [next(it) for _ in range(M)]

            w = dish_idx - 1
            p = len(prev_vals)

            pref = [0] * p
            suff = [0] * p

            running = NEG
            for i in range(p):
                value = prev_best[i] - w * prev_vals[i]
                if value > running:
                    running = value
                pref[i] = running

            running = NEG
            for i in range(p - 1, -1, -1):
                value = prev_best[i] + w * prev_vals[i]
                if value > running:
                    running = value
                suff[i] = running

            if dish_idx < N:
                dp = {}

                for j in range(M):
                    x = arr[j + 1] if j + 1 < M else arr[0]

                    left_idx = bisect_right(prev_vals, x) - 1
                    best_here = NEG

                    if left_idx >= 0:
                        best_here = pref[left_idx] + w * x

                    right_idx = bisect_left(prev_vals, x)
                    if right_idx < p:
                        candidate = suff[right_idx] - w * x
                        if candidate > best_here:
                            best_here = candidate

                    last_value = arr[j]
                    old = dp.get(last_value)
                    if old is None or best_here > old:
                        dp[last_value] = best_here

                items = sorted(dp.items())
                prev_vals = [v for v, _ in items]
                prev_best = [best for _, best in items]

            else:
                best_answer = NEG

                for x in arr:
                    left_idx = bisect_right(prev_vals, x) - 1
                    best_here = NEG

                    if left_idx >= 0:
                        best_here = pref[left_idx] + w * x

                    right_idx = bisect_left(prev_vals, x)
                    if right_idx < p:
                        candidate = suff[right_idx] - w * x
                        if candidate > best_here:
                            best_here = candidate

                    if best_here > best_answer:
                        best_answer = best_here

                ans = best_answer

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()