import sys
from collections import deque


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    H = int(data[0])
    W = int(data[1])

    rows = data[2:2 + H]

    idx = 2 + H
    A = int(data[idx]) - 1
    B = int(data[idx + 1]) - 1
    C = int(data[idx + 2]) - 1
    D = int(data[idx + 3]) - 1

    # 1 for initially road '.', 0 for wall '#'
    trans = bytes.maketrans(b".#", b"\x01\x00")
    road = bytearray(b"".join(rows).translate(trans))

    N = H * W
    start = A * W + B
    target = C * W + D

    dist = [-1] * N
    visited = bytearray(N)
    dist[start] = 0

    dq = deque([start])
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while dq:
        u = dq.popleft()

        if visited[u]:
            continue
        visited[u] = 1

        du = dist[u]
        if u == target:
            print(du)
            return

        r = u // W
        c = u % W

        # Move through cells that are already roads.
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < H and 0 <= nc < W:
                v = nr * W + nc
                if road[v] and not visited[v]:
                    if dist[v] == -1 or dist[v] > du:
                        dist[v] = du
                        dq.appendleft(v)

        # Perform one front kick.
        nd = du + 1
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < H and 0 <= nc < W:
                v = nr * W + nc
                if not visited[v] and (dist[v] == -1 or dist[v] > nd):
                    dist[v] = nd
                    dq.append(v)

            nr = r + 2 * dr
            nc = c + 2 * dc
            if 0 <= nr < H and 0 <= nc < W:
                v = nr * W + nc
                if not visited[v] and (dist[v] == -1 or dist[v] > nd):
                    dist[v] = nd
                    dq.append(v)


if __name__ == "__main__":
    solve()