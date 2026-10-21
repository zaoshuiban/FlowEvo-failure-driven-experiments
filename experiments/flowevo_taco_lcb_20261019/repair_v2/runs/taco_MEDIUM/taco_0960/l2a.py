import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        pos = [0] * (n + 1)

        for i in range(n):
            value = next(it)
            pos[value] = i

        ans = 0

        for v in range(1, n):
            if pos[v] > pos[v + 1]:
                ans = max(ans, min(v, n - v))

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()