import sys

MAXV = 1_000_000
NEG = -10**60

g_arr = [0] * (MAXV + 1)
dp_arr = [0] * (MAXV + 1)


def transform(prev_vals, prev_dp, w, cur):
    m = len(prev_vals)
    M = len(cur)

    if M == 1:
        a = cur[0]
        if m == 1:
            d = prev_vals[0] - a
            if d < 0:
                d = -d
            return [a], [prev_dp[0] + w * d]

        best = NEG
        for i in range(m):
            d = prev_vals[i] - a
            if d < 0:
                d = -d
            cand = prev_dp[i] + w * d
            if cand > best:
                best = cand
        return [a], [best]

    distinct = sorted(set(cur))

    if m == 1:
        x = prev_vals[0]
        base = prev_dp[0]

        for b in distinct:
            dp_arr[b] = NEG

        last = M - 1
        for j in range(M):
            a = cur[j]
            b = cur[j + 1] if j < last else cur[0]

            d = x - b
            if d < 0:
                d = -d

            cand = base + w * d
            if cand > dp_arr[a]:
                dp_arr[a] = cand

        return distinct, [dp_arr[v] for v in distinct]

    # Left side: max over prev_vals <= b
    ptr = -1
    best = NEG
    for b in distinct:
        while ptr + 1 < m and prev_vals[ptr + 1] <= b:
            ptr += 1
            val = prev_dp[ptr] - w * prev_vals[ptr]
            if val > best:
                best = val

        if ptr >= 0:
            g_arr[b] = w * b + best
        else:
            g_arr[b] = NEG

    # Right side: max over prev_vals >= b
    ptr = m
    best = NEG
    for idx in range(len(distinct) - 1, -1, -1):
        b = distinct[idx]

        while ptr - 1 >= 0 and prev_vals[ptr - 1] >= b:
            ptr -= 1
            val = prev_dp[ptr] + w * prev_vals[ptr]
            if val > best:
                best = val

        if ptr < m:
            cand = -w * b + best
            if cand > g_arr[b]:
                g_arr[b] = cand

    for b in distinct:
        dp_arr[b] = NEG

    last = M - 1
    for j in range(M):
        a = cur[j]
        b = cur[j + 1] if j < last else cur[0]

        cand = g_arr[b]
        if cand > dp_arr[a]:
            dp_arr[a] = cand

    return distinct, [dp_arr[v] for v in distinct]


def final_max(prev_vals, prev_dp, w, cur):
    m = len(prev_vals)

    if m == 1:
        x = prev_vals[0]
        base = prev_dp[0]
        maxd = 0

        for b in cur:
            d = x - b
            if d < 0:
                d = -d
            if d > maxd:
                maxd = d

        return base + w * maxd

    if len(cur) == 1:
        b = cur[0]
        best = NEG

        for i in range(m):
            d = prev_vals[i] - b
            if d < 0:
                d = -d
            cand = prev_dp[i] + w * d
            if cand > best:
                best = cand

        return best

    distinct = sorted(set(cur))
    ans = NEG

    # Left side: max over prev_vals <= b
    ptr = -1
    best = NEG
    for b in distinct:
        while ptr + 1 < m and prev_vals[ptr + 1] <= b:
            ptr += 1
            val = prev_dp[ptr] - w * prev_vals[ptr]
            if val > best:
                best = val

        if ptr >= 0:
            cand = w * b + best
            if cand > ans:
                ans = cand

    # Right side: max over prev_vals >= b
    ptr = m
    best = NEG
    for idx in range(len(distinct) - 1, -1, -1):
        b = distinct[idx]

        while ptr - 1 >= 0 and prev_vals[ptr - 1] >= b:
            ptr -= 1
            val = prev_dp[ptr] + w * prev_vals[ptr]
            if val > best:
                best = val

        if ptr < m:
            cand = -w * b + best
            if cand > ans:
                ans = cand

    return ans


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    L = len(data)

    def next_int():
        nonlocal idx
        while idx < L and data[idx] <= 32:
            idx += 1

        num = 0
        while idx < L and data[idx] > 32:
            num = num * 10 + data[idx] - 48
            idx += 1

        return num

    T = next_int()
    answers = []

    for _ in range(T):
        N = next_int()

        if N == 0:
            answers.append("0")
            continue

        if N == 1:
            M = next_int()
            for _ in range(M):
                next_int()
            answers.append("0")
            continue

        M = next_int()
        first_dish = [0] * M
        for j in range(M):
            first_dish[j] = next_int()

        prev_vals = sorted(set(first_dish))
        prev_dp = [0] * len(prev_vals)
        del first_dish

        for i in range(2, N + 1):
            M = next_int()
            cur = [0] * M
            for j in range(M):
                cur[j] = next_int()

            w = i - 1

            if i < N:
                prev_vals, prev_dp = transform(prev_vals, prev_dp, w, cur)
            else:
                answers.append(str(final_max(prev_vals, prev_dp, w, cur)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()