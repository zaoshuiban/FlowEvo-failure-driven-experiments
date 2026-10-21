import sys
from array import array


def main():
    data = sys.stdin.buffer.read()
    p = 0
    ld = len(data)

    def read_int():
        nonlocal p
        while p < ld and data[p] <= 32:
            p += 1
        num = 0
        while p < ld and data[p] > 32:
            num = num * 10 + (data[p] - 48)
            p += 1
        return num

    t = read_int()
    answers = []

    for _ in range(t):
        n = read_int()
        m = read_int()
        total = n * m

        nxt = array('i', [0]) * total

        row = 0
        col = 0
        last_col = m - 1
        last_row = n - 1

        for i in range(total):
            while data[p] <= 32:
                p += 1

            ch = data[p]
            p += 1

            if ch == 76:  # L
                nxt[i] = i - 1 if col else total
            elif ch == 82:  # R
                nxt[i] = i + 1 if col < last_col else total
            elif ch == 85:  # U
                nxt[i] = i - m if row else total
            else:  # D
                nxt[i] = i + m if row < last_row else total

            col += 1
            if col == m:
                col = 0
                row += 1

        dp = array('i', [0]) * total

        max_dist = 0
        best = 0

        for start in range(total):
            if dp[start] != 0:
                continue

            u = start
            length = 0

            while u != total and dp[u] == 0:
                dp[u] = -(length + 1)
                length += 1
                u = nxt[u]

            if u == total:
                base = 0
                is_cycle = False
            else:
                value = dp[u]
                if value > 0:
                    base = value
                    is_cycle = False
                else:
                    is_cycle = True
                    cycle_start_pos = -value - 1

            if is_cycle:
                L = length
                if L > max_dist:
                    max_dist = L
                    best = start

                v = start
                cur = L

                for _ in range(cycle_start_pos):
                    dp[v] = cur
                    cur -= 1
                    v = nxt[v]

                cycle_value = L - cycle_start_pos

                for _ in range(L - cycle_start_pos):
                    dp[v] = cycle_value
                    v = nxt[v]

            else:
                L = length
                start_value = L + base

                if start_value > max_dist:
                    max_dist = start_value
                    best = start

                v = start
                cur = start_value

                for _ in range(L):
                    dp[v] = cur
                    cur -= 1
                    v = nxt[v]

        r = best // m + 1
        c = best % m + 1
        answers.append(f"{r} {c} {max_dist}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()