import sys
from collections import deque


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

        # Multi-source BFS from all friends.
        dist = [-1] * (n + 1)
        q = deque()

        for x in friends:
            dist[x] = 0
            q.append(x)

        while q:
            u = q.popleft()
            nd = dist[u] + 1
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = nd
                    q.append(v)

        # Root the tree at room 1.
        parent = [0] * (n + 1)
        depth = [0] * (n + 1)
        parent[1] = -1

        order = [1]
        ptr = 0
        while ptr < len(order):
            u = order[ptr]
            ptr += 1

            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    depth[v] = depth[u] + 1
                    order.append(v)

        # dp[u] = minimum number of friends needed to block the subtree of u.
        dp = [0] * (n + 1)

        for u in reversed(order):
            if dist[u] <= depth[u]:
                dp[u] = 1
            elif u != 1 and len(adj[u]) == 1:
                dp[u] = INF
            else:
                total = 0
                for v in adj[u]:
                    if v != parent[u]:
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