import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        x = data[idx + 1]
        idx += 2

        degree = [0] * (n + 1)

        for _ in range(n - 1):
            u = data[idx]
            v = data[idx + 1]
            idx += 2
            degree[u] += 1
            degree[v] += 1

        if degree[x] <= 1 or n % 2 == 0:
            answers.append("Ayush")
        else:
            answers.append("Ashish")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()