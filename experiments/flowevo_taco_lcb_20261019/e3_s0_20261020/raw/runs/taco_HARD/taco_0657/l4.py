import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    idx = 0
    L = len(data)

    def next_int() -> int:
        nonlocal idx
        while idx < L and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < L and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    T = next_int()
    answers = []
    NEG = -10**60

    for _ in range(T):
        N = next_int()

        m1 = next_int()
        prev_vals = [0] * m1
        for j in range(m1):
            prev_vals[j] = next_int()

        if N == 1:
            answers.append("0")
            continue

        # For dish 1, the only relevant value is its last ingredient.
        prev_dp = [0] * m1

        for i in range(2, N + 1):
            mcur = next_int()
            weight = i - 1

            if i == N:
                # Last dish: only its first ingredient matters.
                mn = 10**30
                mx = -10**30

                for _ in range(mcur):
                    v = next_int()
                    if v < mn:
                        mn = v
                    if v > mx:
                        mx = v

                c1 = NEG
                c2 = NEG

                for x, dpv in zip(prev_vals, prev_dp):
                    val = dpv - weight * x
                    if val > c1:
                        c1 = val

                    val = dpv + weight * x
                    if val > c2:
                        c2 = val

                ans1 = c1 + weight * mx
                ans2 = c2 - weight * mn
                answers.append(str(ans1 if ans1 > ans2 else ans2))
                break

            cur = [0] * mcur
            for j in range(mcur):
                cur[j] = next_int()

            c1 = NEG
            c2 = NEG

            for x, dpv in zip(prev_vals, prev_dp):
                val = dpv - weight * x
                if val > c1:
                    c1 = val

                val = dpv + weight * x
                if val > c2:
                    c2 = val

            if mcur == 1:
                a = cur[0]
                f1 = c1 + weight * a
                f2 = c2 - weight * a
                best = f1 if f1 > f2 else f2

                prev_vals = [a]
                prev_dp = [best]
            else:
                dp_dict = {}

                # If a is the last ingredient, its successor is the first ingredient.
                for j in range(mcur):
                    a = cur[j]
                    b = cur[j + 1] if j + 1 < mcur else cur[0]

                    f1 = c1 + weight * b
                    f2 = c2 - weight * b
                    cand = f1 if f1 > f2 else f2

                    old = dp_dict.get(a)
                    if old is None or cand > old:
                        dp_dict[a] = cand

                prev_vals = list(dp_dict.keys())
                prev_dp = list(dp_dict.values())

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()