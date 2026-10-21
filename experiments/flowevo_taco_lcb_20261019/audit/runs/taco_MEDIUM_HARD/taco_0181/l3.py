import sys

MOD = 998244353
MAXN = 300000

pow2 = [1] * (MAXN + 5)
for i in range(1, MAXN + 5):
    pow2[i] = (pow2[i - 1] * 2) % MOD


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        graph = [[] for _ in range(n)]

        for _ in range(m):
            u = data[idx] - 1
            v = data[idx + 1] - 1
            idx += 2
            graph[u].append(v)
            graph[v].append(u)

        color = [-1] * n
        answer = 1
        possible = True

        for start in range(n):
            if color[start] != -1:
                continue

            color[start] = 0
            stack = [start]
            count = [1, 0]

            while stack:
                u = stack.pop()

                for v in graph[u]:
                    if color[v] == -1:
                        color[v] = color[u] ^ 1
                        count[color[v]] += 1
                        stack.append(v)
                    elif color[v] == color[u]:
                        possible = False

            if not possible:
                answer = 0
                break

            ways = (pow2[count[0]] + pow2[count[1]]) % MOD
            answer = (answer * ways) % MOD

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()