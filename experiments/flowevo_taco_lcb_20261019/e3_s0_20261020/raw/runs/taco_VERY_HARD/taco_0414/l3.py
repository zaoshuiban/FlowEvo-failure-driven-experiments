import sys
from bisect import bisect_left

INF = 10 ** 15


def update_costs(cand_x, cand_c, opp_x, opp_c, K):
    nc = len(cand_x)
    no = len(opp_x)

    res = [INF] * nc
    dq = [0] * no

    head = 0
    tail = 0

    add_ptr = 0
    rem_ptr = 0
    less_ptr = 0
    prefix_min = INF

    for i in range(nc):
        x = cand_x[i]

        while less_ptr < no and opp_x[less_ptr] < x:
            v = opp_c[less_ptr]
            if v < prefix_min:
                prefix_min = v
            less_ptr += 1

        upper = x + K
        while add_ptr < no and opp_x[add_ptr] <= upper:
            v = opp_c[add_ptr]
            while tail > head and opp_c[dq[tail - 1]] >= v:
                tail -= 1
            dq[tail] = add_ptr
            tail += 1
            add_ptr += 1

        while rem_ptr < no and opp_x[rem_ptr] <= x:
            rem_ptr += 1

        while head < tail and dq[head] < rem_ptr:
            head += 1

        best = prefix_min

        if head < tail:
            v = opp_c[dq[head]] + 1
            if v < best:
                best = v

        c = cand_c[i]
        if c < INF and best < INF:
            res[i] = c + best

    return res


def merge_sorted(lx, lc, rx, rc):
    n1 = len(lx)
    n2 = len(rx)
    total = n1 + n2

    xs = [0] * total
    cs = [0] * total

    i = 0
    j = 0
    idx = 0

    while i < n1 and j < n2:
        if lx[i] < rx[j]:
            xs[idx] = lx[i]
            cs[idx] = lc[i]
            i += 1
        else:
            xs[idx] = rx[j]
            cs[idx] = rc[j]
            j += 1
        idx += 1

    while i < n1:
        xs[idx] = lx[i]
        cs[idx] = lc[i]
        i += 1
        idx += 1

    while j < n2:
        xs[idx] = rx[j]
        cs[idx] = rc[j]
        j += 1
        idx += 1

    return xs, cs


def solve_case(H, K, arr):
    n = 1 << H

    cur = [([arr[i]], [0]) for i in range(n)]

    while len(cur) > 1:
        nxt = []
        append = nxt.append

        for p in range(0, len(cur), 2):
            lx, lc = cur[p]
            rx, rc = cur[p + 1]

            new_lc = update_costs(lx, lc, rx, rc, K)
            new_rc = update_costs(rx, rc, lx, lc, K)

            xs, cs = merge_sorted(lx, new_lc, rx, new_rc)
            append((xs, cs))

        cur = nxt

    xs, cs = cur[0]
    pos = bisect_left(xs, arr[0])

    ans = cs[pos]
    return -1 if ans >= INF else ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        H = data[idx]
        K = data[idx + 1]
        idx += 2

        n = 1 << H
        arr = data[idx:idx + n]
        idx += n

        answers.append(str(solve_case(H, K, arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()