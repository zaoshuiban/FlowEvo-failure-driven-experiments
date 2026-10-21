import sys

MOD = 998244353
MAXN = 300000

pow2 = [1] * (MAXN + 1)
for i in range(1, MAXN + 1):
    pow2[i] = (pow2[i - 1] * 2) % MOD


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    in_number = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_number = True
        else:
            if in_number:
                yield num
                num = 0
                in_number = False

    if in_number:
        yield num


def main():
    it = int_generator()
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        graph = [[] for _ in range(n)]

        for _ in range(m):
            u = next(it) - 1
            v = next(it) - 1
            graph[u].append(v)
            graph[v].append(u)

        color = [-1] * n
        answer = 1

        for start in range(n):
            if color[start] != -1:
                continue

            color[start] = 0
            stack = [start]

            count0 = 1
            count1 = 0
            bipartite = True

            while stack:
                u = stack.pop()
                next_color = color[u] ^ 1

                for v in graph[u]:
                    if color[v] == -1:
                        color[v] = next_color
                        if next_color == 0:
                            count0 += 1
                        else:
                            count1 += 1
                        stack.append(v)
                    elif color[v] == color[u]:
                        bipartite = False

            if not bipartite:
                answer = 0
            else:
                ways = (pow2[count0] + pow2[count1]) % MOD
                answer = (answer * ways) % MOD

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()