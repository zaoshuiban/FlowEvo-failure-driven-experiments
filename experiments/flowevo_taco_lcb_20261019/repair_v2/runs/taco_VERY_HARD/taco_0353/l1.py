import sys


def int_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False
    for c in data:
        if c >= 48:  # digit
            num = num * 10 + (c - 48)
            in_num = True
        else:
            if in_num:
                yield num
                num = 0
                in_num = False
    if in_num:
        yield num


def solve():
    it = int_stream()
    try:
        t = next(it)
    except StopIteration:
        return

    out = []
    INF = 10**18
    NEG = -10**18

    for _ in range(t):
        n = next(it)
        m = next(it)

        rows = []
        for _ in range(n):
            rows.append([next(it) for _ in range(m)])

        order = list(range(n))
        order.sort(key=lambda i: rows[i][0])

        sorted_rows = [rows[i] for i in order]

        size = n * m
        suff_min = [0] * size
        suff_max = [0] * size

        for i, row in enumerate(sorted_rows):
            base = i * m
            cur_min = INF
            cur_max = NEG

            for j in range(m - 1, -1, -1):
                v = row[j]
                if v < cur_min:
                    cur_min = v
                if v > cur_max:
                    cur_max = v

                suff_min[base + j] = cur_min
                suff_max[base + j] = cur_max

        left_min = [INF] * n
        left_max = [NEG] * n

        suf_l = [0] * (n + 1)
        suf_r = [0] * (n + 1)

        found = False
        found_p = -1
        found_k = -1

        for k in range(1, m):
            col = k - 1

            for i in range(n):
                v = sorted_rows[i][col]
                if v < left_min[i]:
                    left_min[i] = v
                if v > left_max[i]:
                    left_max[i] = v

            min_l = INF
            max_r = NEG

            for i in range(n - 1, -1, -1):
                v = left_min[i]
                if v < min_l:
                    min_l = v
                suf_l[i] = min_l

                v = suff_max[i * m + k]
                if v > max_r:
                    max_r = v
                suf_r[i] = max_r

            pref_max_l = NEG
            pref_min_r = INF

            for p in range(1, n):
                i = p - 1

                v = left_max[i]
                if v > pref_max_l:
                    pref_max_l = v

                v = suff_min[i * m + k]
                if v < pref_min_r:
                    pref_min_r = v

                if pref_max_l < suf_l[p] and pref_min_r > suf_r[p]:
                    found = True
                    found_p = p
                    found_k = k
                    break

            if found:
                break

        if not found:
            out.append("NO")
        else:
            colors = ['R'] * n
            for pos in range(found_p):
                colors[order[pos]] = 'B'

            out.append("YES")
            out.append(''.join(colors) + ' ' + str(found_k))

    sys.stdout.write('\n'.join(out))


if __name__ == "__main__":
    solve()