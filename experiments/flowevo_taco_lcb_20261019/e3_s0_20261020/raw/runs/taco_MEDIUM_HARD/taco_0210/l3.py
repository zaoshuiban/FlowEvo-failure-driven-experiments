import sys


def solve() -> None:
    data = sys.stdin.buffer.readline().strip()
    if not data:
        return

    k = int(data)

    def c2(x: int) -> int:
        return x * (x - 1) // 2

    def c3(x: int) -> int:
        return x * (x - 1) * (x - 2) // 6

    # Largest clique whose number of triangles does not exceed k.
    a = 3
    while c3(a + 1) <= k:
        a += 1

    remaining = k - c3(a)

    # Represent remaining as a sum of numbers C(t, 2).
    # Each such term will correspond to a new vertex connected to t clique vertices.
    terms = []

    if remaining > 0:
        INF = 10**9
        dp = [INF] * (remaining + 1)
        prev_sum = [0] * (remaining + 1)
        used_t = [0] * (remaining + 1)

        dp[0] = 0

        for s in range(1, remaining + 1):
            for t in range(2, a + 1):
                value = c2(t)
                if value > s:
                    break

                if dp[s - value] + 1 < dp[s]:
                    dp[s] = dp[s - value] + 1
                    prev_sum[s] = s - value
                    used_t[s] = t

        cur = remaining
        while cur > 0:
            terms.append(used_t[cur])
            cur = prev_sum[cur]

    n = a + len(terms)
    graph = [['0'] * n for _ in range(n)]

    # Build a clique of size a.
    for i in range(a):
        for j in range(i + 1, a):
            graph[i][j] = '1'
            graph[j][i] = '1'

    # Add extra vertices. Each one is connected to t vertices of the clique.
    for idx, t in enumerate(terms):
        v = a + idx
        for u in range(t):
            graph[v][u] = '1'
            graph[u][v] = '1'

    result = [str(n)]
    result.extend(''.join(row) for row in graph)

    sys.stdout.write('\n'.join(result))


if __name__ == "__main__":
    solve()