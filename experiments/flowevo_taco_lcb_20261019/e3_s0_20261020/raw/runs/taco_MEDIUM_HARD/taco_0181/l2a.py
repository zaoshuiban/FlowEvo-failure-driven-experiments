import sys

MOD = 998244353
MAXN = 300005


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    pow2 = [1] * MAXN
    for i in range(1, MAXN):
        pow2[i] = (pow2[i - 1] * 2) % MOD

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        adj = [[] for _ in range(n)]

        for _ in range(m):
            u = data[idx] - 1
            v = data[idx + 1] - 1
            idx += 2
            adj[u].append(v)
            adj[v].append(u)

        color = [-1] * n
        ans = 1
        possible = True

        for start in range(n):
            if color[start] != -1:
                continue

            color[start] = 0
            stack = [start]
            cnt = [1, 0]

            while stack:
                u = stack.pop()
                cu = color[u]

                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = cu ^ 1
                        cnt[color[v]] += 1
                        stack.append(v)
                    elif color[v] == cu:
                        possible = False

            if possible:
                ways = (pow2[cnt[0]] + pow2[cnt[1]]) % MOD
                ans = (ans * ways) % MOD

        if not possible:
            ans = 0

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()