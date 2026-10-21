import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        current = 0
        best_red = 0
        for _ in range(n):
            current += next(it)
            best_red = max(best_red, current)

        m = next(it)

        current = 0
        best_blue = 0
        for _ in range(m):
            current += next(it)
            best_blue = max(best_blue, current)

        answers.append(str(best_red + best_blue))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()