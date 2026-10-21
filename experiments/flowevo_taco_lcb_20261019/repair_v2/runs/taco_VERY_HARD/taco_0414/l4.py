import sys

INF = 10 ** 15


def update_filtered(cx, cc, ox, oc, K):
    """
    For every possible winner x from one child (cx, cc), compute the minimum
    additional cost needed to make x win against the other child, whose possible
    winners are (ox, oc). Only finite results are returned.
    """
    m = len(ox)
    res_x = []
    res_c = []
    if m == 0:
        return res_x, res_c

    dq = [0] * m
    head = tail = 0
    add_ptr = 0
    less_ptr = 0
    rem_ptr = 0
    prefix_min = INF

    for i in range(len(cx)):
        x = cx[i]

        # Opponents weaker than x: no bribe is needed.
        while less_ptr < m and ox[less_ptr] < x:
            v = oc[less_ptr]
            if v < prefix_min:
                prefix_min = v
            less_ptr += 1

        # Opponents that can be beaten by bribing: x < y <= x + K.
        upper = x + K
        while add_ptr < m and ox[add_ptr] <= upper:
            v = oc[add_ptr]
            while tail > head and oc[dq[tail - 1]] >= v:
                tail -= 1
            dq[tail] = add_ptr
            tail += 1
            add_ptr += 1

        # Remove opponents y <= x, because they belong to the no-bribe case.
        while rem_ptr < m and ox[rem_ptr] <= x:
            rem_ptr += 1

        while head < tail and dq[head] < rem_ptr:
            head += 1

        best = prefix_min

        if head < tail:
            v = oc[dq[head]] + 1
            if v < best:
                best = v

        if best < INF:
            res_x.append(x)
            res_c.append(cc[i] + best)

    return res_x, res_c


def merge_sorted(lx, lc, rx, rc):
    n1 = len(lx)
    n2 = len(rx)

    if n1 == 0:
        return rx, rc
    if n2 == 0:
        return lx, lc

    total = n1 + n2
    xs = [0] * total
    cs = [0] * total

    i = j = k = 0
    while i < n1 and j < n2:
        if lx[i] < rx[j]:
            xs[k] = lx[i]
            cs[k] = lc[i]
            i += 1
        else:
            xs[k] = rx[j]
            cs[k] = rc[j]
            j += 1
        k += 1

    while i < n1:
        xs[k] = lx[i]
        cs[k] = lc[i]
        i += 1
        k += 1

    while j < n2:
        xs[k] = rx[j]
        cs[k] = rc[j]
        j += 1
        k += 1

    return xs, cs


def solve_case(H, K, arr):
    n = 1 << H
    limak = arr[0]

    # Stage 1: Limak directly fights bear 2, i.e. arr[1].
    y = arr[1]
    if limak > y:
        stage_cost = 0
    elif y - limak <= K:
        stage_cost = 1
    else:
        return -1

    ans = stage_cost

    if H == 1:
        return ans

    # Build all blocks of size 2 that do not contain Limak.
    # At level l, current stores active blocks of size 2^l.
    current = []

    for start in range(2, n, 2):
        a = arr[start]
        b = arr[start + 1]

        if a < b:
            low, high = a, b
        else:
            low, high = b, a

        if high - low <= K:
            # low can win by one bribe, high wins without bribe
            current.append(([low, high], [1, 0]))
        else:
            # only high can win this block
            current.append(([high], [0]))

    size = 2
    level = 1

    while True:
        # current[0] is exactly the opponent block for this stage.
        xs, cs = current[0]
        best = INF

        for i in range(len(xs)):
            y = xs[i]

            if limak > y:
                extra = 0
            else:
                if y - limak <= K:
                    extra = 1
                else:
                    continue

            val = cs[i] + extra
            if val < best:
                best = val

        if best >= INF:
            return -1

        ans += best

        if level == H - 1:
            break

        # Build active blocks of the next size.
        nxt = []
        idx = 1
        cur_len = len(current)

        while idx + 1 < cur_len:
            lx, lc = current[idx]
            rx, rc = current[idx + 1]

            nlx, nlc = update_filtered(lx, lc, rx, rc, K)
            nrx, nrc = update_filtered(rx, rc, lx, lc, K)

            mxs, mcs = merge_sorted(nlx, nlc, nrx, nrc)
            nxt.append((mxs, mcs))

            idx += 2

        current = nxt
        size <<= 1
        level += 1

    return ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        H = data[pos]
        K = data[pos + 1]
        pos += 2

        n = 1 << H
        arr = data[pos:pos + n]
        pos += n

        answers.append(str(solve_case(H, K, arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()