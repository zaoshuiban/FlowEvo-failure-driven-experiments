import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []
    INF = 10**9

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        friends = data[idx:idx + k]
        idx += k

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = data[idx]
            v = data[idx + 1]
            idx += 2
            adj[u].append(v)
            adj[v].append(u)

        parent = [0] * (n + 1)
        depth = [0] * (n + 1)
        order = [1]
        parent[1] = 0

        pos = 0
        while pos < len(order):
            u = order[pos]
            pos += 1

            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    depth[v] = depth[u] + 1
                    order.append(v)

        down = [INF] * (n + 1)
        for x in friends:
            down[x] = 0

        # Minimum distance to a friend inside each subtree.
        for i in range(n - 1, 0, -1):
            u = order[i]
            p = parent[u]
            val = down[u] + 1
            if val < down[p]:
                down[p] = val

        # Convert to minimum distance from any friend.
        for i in range(1, n):
            u = order[i]
            p = parent[u]
            val = down[p] + 1
            if val < down[u]:
                down[u] = val

        dp = [0] * (n + 1)
        answer = INF

        for i in range(n - 1, -1, -1):
            u = order[i]

            if down[u] <= depth[u]:
                cur = 1
            elif u != 1 and len(adj[u]) == 1:
                cur = INF
            else:
                cur = dp[u]
                if cur > INF:
                    cur = INF

            if u == 1:
                answer = cur
            else:
                p = parent[u]
                total = dp[p] + cur
                dp[p] = total if total < INF else INF

        if answer >= INF:
            answers.append("-1")
        else:
            answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()