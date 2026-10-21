import sys


def solve() -> None:
    data = sys.stdin.read().strip().split()
    if not data:
        return

    n = int(data[0])
    q, r = divmod(n, 10)

    digits = list(map(int, str(q)))  # q >= 0; str(0) == "0"
    L = len(digits)

    # agg_next[length][pmax][u]
    # agg_cost[length][pmax][u]
    # Process all suffixes of given length in descending order,
    # where the maximum digit of the fixed prefix is pmax,
    # starting from unit digit/state u.
    agg_next = [[None for _ in range(10)] for _ in range(L + 1)]
    agg_cost = [[None for _ in range(10)] for _ in range(L + 1)]

    # Length 0: one fixed number whose maximum digit is pmax.
    for pmax in range(10):
        nxt = [0] * 10
        cost = [0] * 10
        for u in range(10):
            if pmax == 0:
                nxt[u] = u
                cost[u] = 0
            elif u >= pmax:
                nxt[u] = 10 - pmax
                cost[u] = 2
            else:
                nxt[u] = u + 10 - pmax
                cost[u] = 1
        agg_next[0][pmax] = nxt
        agg_cost[0][pmax] = cost

    for length in range(1, L + 1):
        for pmax in range(10):
            nxt = [0] * 10
            cost = [0] * 10

            for start_u in range(10):
                u = start_u
                total = 0

                for d in range(9, -1, -1):
                    new_pmax = max(pmax, d)
                    block_next = agg_next[length - 1][new_pmax]
                    block_cost = agg_cost[length - 1][new_pmax]

                    total += block_cost[u]
                    u = block_next[u]

                nxt[start_u] = u
                cost[start_u] = total

            agg_next[length][pmax] = nxt
            agg_cost[length][pmax] = cost

    def dfs(pos: int, pmax: int, u: int):
        if pos == L:
            if pmax == 0:
                return u, 0
            if u >= pmax:
                return 10 - pmax, 2
            return u + 10 - pmax, 1

        cur_digit = digits[pos]

        # First process numbers with the same prefix and same current digit.
        u, cost = dfs(pos + 1, max(pmax, cur_digit), u)

        remaining = L - pos - 1

        # Then process smaller digits at this position in descending order.
        for d in range(cur_digit - 1, -1, -1):
            new_pmax = max(pmax, d)
            block_next = agg_next[remaining][new_pmax]
            block_cost = agg_cost[remaining][new_pmax]

            cost += block_cost[u]
            u = block_next[u]

        return u, cost

    final_digit, operations = dfs(0, 0, r)
    if final_digit > 0:
        operations += 1

    print(operations)


if __name__ == "__main__":
    solve()