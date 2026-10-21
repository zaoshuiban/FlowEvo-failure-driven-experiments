import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    q = next(it)
    answers = []

    for _ in range(q):
        n = next(it)
        t = [next(it) for _ in range(n)]
        t.sort()

        max_time = 2 * n + 5
        INF = 10**9

        prev = [0] * (max_time + 1)

        for i in range(1, n + 1):
            cur = [INF] * (max_time + 1)
            for time in range(1, max_time + 1):
                cur[time] = min(
                    cur[time - 1],
                    prev[time - 1] + abs(t[i - 1] - time)
                )
            prev = cur

        answers.append(str(prev[max_time]))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()