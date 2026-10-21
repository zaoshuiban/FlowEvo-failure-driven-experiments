import sys


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    ndata = len(data)

    def next_int():
        nonlocal idx
        while idx < ndata and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < ndata and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []
    INF = 10**30

    for _ in range(t):
        n = next_int()
        q = next_int()

        cycles = []

        for _ in range(n):
            a = next_int()
            pos = [0] * (a + 1)
            total = 0

            for v in range(1, a + 1):
                w = next_int()
                total += w
                if v < a:
                    pos[v + 1] = pos[v] + w

            cycles.append((a, total, pos))

        conn_u = [0] * n
        conn_v = [0] * n
        conn_w = [0] * n

        for i in range(n):
            conn_u[i] = next_int()
            conn_v[i] = next_int()
            conn_w[i] = next_int()

        left = [0] * n
        right = conn_u

        for i in range(n):
            left[i] = conn_v[(i - 1) % n]

        pos_left = [0] * n
        pos_right = [0] * n

        current = 0

        for i in range(n):
            pos_left[i] = current

            a, total, pos = cycles[i]
            l = left[i]
            r = right[i]

            d = pos[l] - pos[r]
            if d < 0:
                d = -d
            other = total - d
            internal_dist = d if d < other else other

            current += internal_dist
            pos_right[i] = current
            current += conn_w[i]

        cycle_total = current

        def cycle_distance(total, pos, u, v):
            d = pos[u] - pos[v]
            if d < 0:
                d = -d
            other = total - d
            return d if d < other else other

        def ring_distance(a, b):
            d = a - b
            if d < 0:
                d = -d
            other = cycle_total - d
            return d if d < other else other

        for _ in range(q):
            v1 = next_int()
            c1 = next_int() - 1
            v2 = next_int()
            c2 = next_int() - 1

            _, total1, pos1 = cycles[c1]
            _, total2, pos2 = cycles[c2]

            l1 = left[c1]
            r1 = right[c1]
            l2 = left[c2]
            r2 = right[c2]

            d1_left = cycle_distance(total1, pos1, v1, l1)
            d1_right = cycle_distance(total1, pos1, v1, r1)

            d2_left = cycle_distance(total2, pos2, v2, l2)
            d2_right = cycle_distance(total2, pos2, v2, r2)

            best = INF

            value = d1_left + ring_distance(pos_left[c1], pos_left[c2]) + d2_left
            if value < best:
                best = value

            value = d1_left + ring_distance(pos_left[c1], pos_right[c2]) + d2_right
            if value < best:
                best = value

            value = d1_right + ring_distance(pos_right[c1], pos_left[c2]) + d2_left
            if value < best:
                best = value

            value = d1_right + ring_distance(pos_right[c1], pos_right[c2]) + d2_right
            if value < best:
                best = value

            answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()