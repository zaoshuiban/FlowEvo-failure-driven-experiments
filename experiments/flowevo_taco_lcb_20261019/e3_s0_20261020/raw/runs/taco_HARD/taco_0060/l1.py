import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

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

        for friend in friends:
            dist[friend] = 0
            q.append(friend)

        while q:
            v = q.popleft()
            nd = dist[v] + 1

            for to in adj[v]:
                if dist[to] == -1:
                    dist[to] = nd
                    q.append(to)

        ans = 0
        can_escape = False

        # Traverse only through vertices Vlad can reach before any friend.
        stack = [(1, 0, 0)]  # vertex, parent, depth

        while stack:
            v, parent, depth = stack.pop()

            # Friend can reach this vertex no later than Vlad.
            if v != 1 and dist[v] <= depth:
                ans += 1
                continue

            # Vlad safely reaches a leaf.
            if v != 1 and len(adj[v]) == 1:
                can_escape = True
                break

            for to in adj[v]:
                if to != parent:
                    stack.append((to, v, depth + 1))

        if can_escape:
            answers.append("-1")
        else:
            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()