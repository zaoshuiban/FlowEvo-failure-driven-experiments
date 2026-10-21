import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []
    INF = 10**9

    for _ in range(t):
        n = next(it)
        k = next(it)

        friends = [next(it) - 1 for _ in range(k)]

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            u = next(it) - 1
            v = next(it) - 1
            adj[u].append(v)
            adj[v].append(u)

        # Minimum distance from every vertex to any friend.
        dist_friend = [INF] * n
        q = deque()

        for x in friends:
            dist_friend[x] = 0
            q.append(x)

        while q:
            v = q.popleft()
            nd = dist_friend[v] + 1
            for to in adj[v]:
                if dist_friend[to] == INF:
                    dist_friend[to] = nd
                    q.append(to)

        # Depth from room 1, and parents for traversal.
        depth = [-1] * n
        parent = [-1] * n
        depth[0] = 0
        parent[0] = -2

        stack = [0]
        while stack:
            v = stack.pop()
            for to in adj[v]:
                if to != parent[v]:
                    parent[to] = v
                    depth[to] = depth[v] + 1
                    stack.append(to)

        answer = 0
        stack = [(0, -1)]

        while stack:
            v, p = stack.pop()

            # A friend can reach this vertex no later than Vlad.
            if dist_friend[v] <= depth[v]:
                answer += 1
                continue

            # Vlad can escape through this leaf before any friend catches him.
            if v != 0 and len(adj[v]) == 1:
                answer = -1
                break

            for to in adj[v]:
                if to != p:
                    stack.append((to, v))

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()