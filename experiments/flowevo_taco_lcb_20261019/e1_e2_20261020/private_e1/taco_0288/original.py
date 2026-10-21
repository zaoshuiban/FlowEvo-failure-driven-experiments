import sys


def integer_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False
    for ch in data:
        if 48 <= ch <= 57:
            num = num * 10 + (ch - 48)
            in_num = True
        else:
            if in_num:
                yield num
                num = 0
                in_num = False
    if in_num:
        yield num


def solve():
    it = iter(integer_stream())
    T = next(it)
    answers = []
    INF = 10**8

    # State index inside a node's DP:
    # k = number of coin children, capped at 2: 0, 1, 2
    # flag = whether any child has a coin child
    # state = k * 2 + flag
    trans = [[0] * 4 for _ in range(6)]
    for state in range(6):
        k = state >> 1
        flag = state & 1
        for cu in (0, 1):
            nk = k + cu
            if nk > 2:
                nk = 2
            for hu in (0, 1):
                opt = (cu << 1) | hu
                nflag = flag | hu
                trans[state][opt] = (nk << 1) | nflag

    for _ in range(T):
        N = next(it)

        adj = [[] for _ in range(N + 1)]
        for _ in range(N - 1):
            u = next(it)
            v = next(it)
            adj[u].append(v)
            adj[v].append(u)

        parent = [0] * (N + 1)
        parent[1] = -1
        order = []
        stack = [1]

        while stack:
            v = stack.pop()
            order.append(v)
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                stack.append(u)

        dp = [None] * (N + 1)

        for v in reversed(order):
            # aggs[p][state], p = 2 * parent_coin + v_coin
            # state = (coin_children_count_capped_at_2) * 2 + any_grandchild_coin
            aggs = []
            for _ in range(4):
                arr = [INF] * 6
                arr[0] = 0
                aggs.append(arr)

            pv = parent[v]

            for u in adj[v]:
                if u == pv:
                    continue

                child_dp = dp[u]

                for p in range(4):
                    base = p << 2
                    opts = (
                        child_dp[base],
                        child_dp[base + 1],
                        child_dp[base + 2],
                        child_dp[base + 3],
                    )

                    cur = aggs[p]
                    new = [INF] * 6

                    for state in range(6):
                        cur_val = cur[state]
                        if cur_val >= INF:
                            continue

                        tr = trans[state]

                        for opt in range(4):
                            opt_val = opts[opt]
                            if opt_val >= INF:
                                continue

                            new_state = tr[opt]
                            new_val = cur_val + opt_val
                            if new_val < new[new_state]:
                                new[new_state] = new_val

                    aggs[p] = new

            cur_dp = [INF] * 16

            for p in range(4):
                b = p >> 1          # parent has coin
                c = p & 1           # current node has coin
                cost = aggs[p]

                if c == 0:
                    # If current node has no coin, it needs two coin neighbours.
                    # h = 1 since it must have at least one coin child.
                    best = INF

                    if b == 1:
                        best = min(best, cost[2], cost[3])

                    best = min(best, cost[4], cost[5])

                    if best < INF:
                        idx = (p << 1) + 1
                        cur_dp[idx] = best
                        cur_dp[8 + idx] = best

                else:
                    # Current node has a coin.
                    any_grandchild_0 = cost[0]
                    any_grandchild_1 = cost[1]

                    best_h1 = min(cost[2], cost[3], cost[4], cost[5])
                    if best_h1 < INF:
                        best_h1 += 1

                    base_idx = p << 1

                    for a in (0, 1):
                        if b or a:
                            best_h0 = min(any_grandchild_0, any_grandchild_1)
                        else:
                            best_h0 = any_grandchild_1

                        if best_h0 < INF:
                            cur_dp[(a << 3) + base_idx] = best_h0 + 1

                        if best_h1 < INF:
                            cur_dp[(a << 3) + base_idx + 1] = best_h1

            dp[v] = cur_dp

        ans = min(dp[1][0:4])

        if ans >= INF:
            answers.append("-1")
        else:
            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()