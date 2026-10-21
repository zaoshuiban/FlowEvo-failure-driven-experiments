import sys


def solve() -> None:
    input = sys.stdin.buffer.readline

    N, M = map(int, input().split())
    V = 2 * N

    # Nodes 0..N-1       : p_i = x_i XOR y_i
    # Nodes N..2N-1      : x_i, where x_i = 0 if honest, 1 if liar
    # y_i = confused flag.
    adj = [[] for _ in range(V)]

    for _ in range(M):
        a, b, c = map(int, input().split())
        a -= 1
        b -= 1

        u = a
        v = N + b

        # Equation: p_a XOR x_b = c
        adj[u].append((v, c))
        adj[v].append((u, c))

    value = [-1] * V

    for start in range(V):
        if value[start] != -1:
            continue

        value[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()
            vu = value[u]

            for v, w in adj[u]:
                expected = vu ^ w

                if value[v] == -1:
                    value[v] = expected
                    stack.append(v)
                elif value[v] != expected:
                    print(-1)
                    return

    ans = []
    for i in range(N):
        p_i = value[i]
        x_i = value[N + i]
        y_i = p_i ^ x_i
        ans.append('1' if y_i else '0')

    print(''.join(ans))


if __name__ == "__main__":
    solve()