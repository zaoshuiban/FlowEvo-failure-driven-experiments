import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))
        grid = [next(it) for _ in range(n)]

        changes = 0

        # Last column: every cell except the bottom one must point Down.
        for i in range(n - 1):
            if grid[i][m - 1] == 'R':
                changes += 1

        # Last row: every cell except the rightmost one must point Right.
        for j in range(m - 1):
            if grid[n - 1][j] == 'D':
                changes += 1

        answers.append(str(changes))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()