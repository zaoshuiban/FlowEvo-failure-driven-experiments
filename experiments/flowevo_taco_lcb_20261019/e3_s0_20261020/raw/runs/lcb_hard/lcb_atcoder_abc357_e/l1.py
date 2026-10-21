import sys
from collections import deque

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N = data[0]
    nxt = [x - 1 for x in data[1:1 + N]]

    indeg = [0] * N
    rev = [[] for _ in range(N)]

    for u, v in enumerate(nxt):
        indeg[v] += 1
        rev[v].append(u)

    # Remove non-cycle vertices by topological pruning.
    q = deque(i for i in range(N) if indeg[i] == 0)
    while q:
        v = q.popleft()
        u = nxt[v]
        indeg[u] -= 1
        if indeg[u] == 0:
            q.append(u)

    # Vertices with indeg > 0 are exactly the cycle vertices.
    comp = [-1] * N
    cycle_len = []

    for i in range(N):
        if indeg[i] > 0 and comp[i] == -1:
            cid = len(cycle_len)
            length = 0
            v = i

            while True:
                comp[v] = cid
                length += 1
                v = nxt[v]
                if v == i:
                    break

            cycle_len.append(length)

    # Propagate component IDs and distances to the cycle through reverse edges.
    depth = [0] * N
    q = deque()

    for i in range(N):
        if indeg[i] > 0:
            q.append(i)

    while q:
        v = q.popleft()
        cid = comp[v]

        for u in rev[v]:
            if comp[u] == -1:
                comp[u] = cid
                depth[u] = depth[v] + 1
                q.append(u)

    ans = 0
    for i in range(N):
        ans += depth[i] + cycle_len[comp[i]]

    print(ans)


if __name__ == "__main__":
    main()