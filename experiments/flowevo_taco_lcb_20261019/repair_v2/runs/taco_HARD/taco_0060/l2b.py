import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []
    INF = 10**9

    for _ in range(t):
        n = int(next(it))
        k = int(next(it))

        is_friend = bytearray(n + 1)
        for _ in range(k):
            x = int(next(it))
            is_friend[x] = 1

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = int(next(it))
            v = int(next(it))
            adj[u].append(v)
            adj[v].append(u)

        available = bytearray(n + 1)
        parent = [0] * (n + 1)
        path = [0] * (n + 1)
        order = []

        stack = [(1, 0, 0)]  # node, parent, depth
        while stack:
            u, p, depth = stack.pop()
            parent[u] = p
            path[depth] = u
            order.append(u)

            if is_friend[u]:
                target_depth = (depth + 1) // 2
                available[path[target_depth]] = 1

            for v in adj[u]:
                if v != p:
                    stack.append((v, u, depth + 1))

        dp = [0] * (n + 1)

        for u in reversed(order):
            if available[u]:
                dp[u] = 1
            elif u != 1 and len(adj[u]) == 1:
                dp[u] = INF
            else:
                total = 0
                pu = parent[u]
                for v in adj[u]:
                    if v != pu:
                        total += dp[v]
                        if total >= INF:
                            total = INF
                            break
                dp[u] = total

        if dp[1] >= INF:
            answers.append("-1")
        else:
            answers.append(str(dp[1]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()