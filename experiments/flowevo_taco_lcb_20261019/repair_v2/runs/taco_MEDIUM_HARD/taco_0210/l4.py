import sys


def solve() -> None:
    data = sys.stdin.buffer.readline()
    if not data:
        return

    k = int(data)
    n = 100

    graph = [['0'] * n for _ in range(n)]

    for i in range(n):
        for j in range(i):
            if k >= j:
                k -= j
                graph[i][j] = graph[j][i] = '1'
            else:
                break

    answer = [str(n)]
    answer.extend(''.join(row) for row in graph)
    sys.stdout.write('\n'.join(answer))


if __name__ == "__main__":
    solve()