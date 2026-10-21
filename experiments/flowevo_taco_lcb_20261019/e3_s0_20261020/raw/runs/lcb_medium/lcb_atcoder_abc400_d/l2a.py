import sys
from collections import deque

def main():
    input = sys.stdin.buffer.readline

    H, W = map(int, input().split())
    grid = b''.join(input().strip() for _ in range(H))
    A, B, C, D = map(int, input().split())

    start = (A - 1) * W + (B - 1)
    goal = (C - 1) * W + (D - 1)

    N = H * W
    INF = 10**9
    dist = [INF] * N
    dist[start] = 0

    dq = deque([start])
    visited = bytearray(N)
    DOT = ord('.')

    while dq:
        v = dq.popleft()
        if visited[v]:
            continue
        visited[v] = 1

        d = dist[v]
        if v == goal:
            print(d)
            return

        r = v // W
        c = v - r * W

        # Move to adjacent original roads with cost 0.
        if r > 0:
            ni = v - W
            if grid[ni] == DOT and dist[ni] > d:
                dist[ni] = d
                dq.appendleft(ni)

        if r + 1 < H:
            ni = v + W
            if grid[ni] == DOT and dist[ni] > d:
                dist[ni] = d
                dq.appendleft(ni)

        if c > 0:
            ni = v - 1
            if grid[ni] == DOT and dist[ni] > d:
                dist[ni] = d
                dq.appendleft(ni)

        if c + 1 < W:
            ni = v + 1
            if grid[ni] == DOT and dist[ni] > d:
                dist[ni] = d
                dq.appendleft(ni)

        nd = d + 1

        # Kick upward.
        if r > 0:
            ni = v - W
            if dist[ni] > nd:
                dist[ni] = nd
                dq.append(ni)

            if r > 1:
                ni = v - 2 * W
                if dist[ni] > nd:
                    dist[ni] = nd
                    dq.append(ni)

        # Kick downward.
        if r + 1 < H:
            ni = v + W
            if dist[ni] > nd:
                dist[ni] = nd
                dq.append(ni)

            if r + 2 < H:
                ni = v + 2 * W
                if dist[ni] > nd:
                    dist[ni] = nd
                    dq.append(ni)

        # Kick leftward.
        if c > 0:
            ni = v - 1
            if dist[ni] > nd:
                dist[ni] = nd
                dq.append(ni)

            if c > 1:
                ni = v - 2
                if dist[ni] > nd:
                    dist[ni] = nd
                    dq.append(ni)

        # Kick rightward.
        if c + 1 < W:
            ni = v + 1
            if dist[ni] > nd:
                dist[ni] = nd
                dq.append(ni)

            if c + 2 < W:
                ni = v + 2
                if dist[ni] > nd:
                    dist[ni] = nd
                    dq.append(ni)

    print(dist[goal])


if __name__ == "__main__":
    main()