import sys


def solve():
    data = sys.stdin.buffer.read()
    L = len(data)
    idx = 0

    def next_int():
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
    INF = 10**30

    for _ in range(T):
        N = next_int()
        Q = next_int()

        pos_cycles = [None] * N
        totals = [0] * N

        for i in range(N):
            A = next_int()
            pos = [0] * (A + 1)

            s = 0
            for v in range(2, A + 1):
                w = next_int()
                s += w
                pos[v] = s

            last_edge = next_int()
            totals[i] = s + last_edge
            pos_cycles[i] = pos

        in_node = [0] * N
        out_node = [0] * N
        inter_weight = [0] * N

        for i in range(N):
            v1 = next_int()
            v2 = next_int()
            w = next_int()

            out_node[i] = v1
            in_node[(i + 1) % N] = v2
            inter_weight[i] = w

        pos_in = [0] * N
        pos_out = [0] * N

        cur = 0
        for i in range(N):
            pos_in[i] = cur

            P = pos_cycles[i]
            S = totals[i]

            u = in_node[i]
            v = out_node[i]

            diff = P[u] - P[v]
            if diff < 0:
                diff = -diff

            other = S - diff
            connector = diff if diff < other else other

            cur += connector
            pos_out[i] = cur
            cur += inter_weight[i]

        total_macro = cur

        for _q in range(Q):
            v1 = next_int()
            c1 = next_int()
            v2 = next_int()
            c2 = next_int()

            c = c1 - 1
            d = c2 - 1

            P = pos_cycles[c]
            S = totals[c]
            pv = P[v1]

            pin = P[in_node[c]]
            diff = pv - pin
            if diff < 0:
                diff = -diff
            other = S - diff
            dist_in_start = diff if diff < other else other

            pout = P[out_node[c]]
            diff = pv - pout
            if diff < 0:
                diff = -diff
            other = S - diff
            dist_out_start = diff if diff < other else other

            P2 = pos_cycles[d]
            S2 = totals[d]
            pv2 = P2[v2]

            pin2 = P2[in_node[d]]
            diff = pv2 - pin2
            if diff < 0:
                diff = -diff
            other = S2 - diff
            dist_in_end = diff if diff < other else other

            pout2 = P2[out_node[d]]
            diff = pv2 - pout2
            if diff < 0:
                diff = -diff
            other = S2 - diff
            dist_out_end = diff if diff < other else other

            ans = INF

            # start at in(c), end at in(d)
            delta = pos_in[c] - pos_in[d]
            if delta < 0:
                delta = -delta
            md = delta
            other = total_macro - delta
            if other < md:
                md = other
            val = dist_in_start + md + dist_in_end
            if val < ans:
                ans = val

            # start at in(c), end at out(d)
            delta = pos_in[c] - pos_out[d]
            if delta < 0:
                delta = -delta
            md = delta
            other = total_macro - delta
            if other < md:
                md = other
            val = dist_in_start + md + dist_out_end
            if val < ans:
                ans = val

            # start at out(c), end at in(d)
            delta = pos_out[c] - pos_in[d]
            if delta < 0:
                delta = -delta
            md = delta
            other = total_macro - delta
            if other < md:
                md = other
            val = dist_out_start + md + dist_in_end
            if val < ans:
                ans = val

            # start at out(c), end at out(d)
            delta = pos_out[c] - pos_out[d]
            if delta < 0:
                delta = -delta
            md = delta
            other = total_macro - delta
            if other < md:
                md = other
            val = dist_out_start + md + dist_out_end
            if val < ans:
                ans = val

            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()