import sys

OFFSETS = []
for K in range(11):
    offsets = []
    for dr in range(-K, K + 1):
        rem = K - abs(dr)
        for dc in range(-rem, rem + 1):
            if dr != 0 or dc != 0:
                offsets.append((dr, dc))
    OFFSETS.append(offsets)


def bfs(start, K, allowed, N, M):
    V = N * M
    dist = [-1] * V
    dist[start] = 0

    queue = [start]
    head = 0
    offsets = OFFSETS[K]

    while head < len(queue):
        u = queue[head]
        head += 1

        r = u // M
        c = u - r * M
        nd = dist[u] + 1

        for dr, dc in offsets:
            nr = r + dr
            if 0 <= nr < N:
                nc = c + dc
                if 0 <= nc < M:
                    v = nr * M + nc
                    if allowed[v] and dist[v] == -1:
                        dist[v] = nd
                        queue.append(v)

    return dist


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        M = next(it)
        K1 = next(it)
        K2 = next(it)

        allowed = [next(it) == 0 for _ in range(N * M)]

        start1 = 0
        start2 = M - 1

        dist1 = bfs(start1, K1, allowed, N, M)
        dist2 = bfs(start2, K2, allowed, N, M)

        ans = 10**9

        for i in range(N * M):
            if allowed[i] and dist1[i] != -1 and dist2[i] != -1:
                ans = min(ans, max(dist1[i], dist2[i]))

        if ans == 10**9:
            answers.append("-1")
        else:
            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()