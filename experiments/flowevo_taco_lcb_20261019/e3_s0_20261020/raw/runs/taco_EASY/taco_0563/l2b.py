import sys

def solve() -> None:
    data = sys.stdin.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        grid = data[idx:idx + n]
        idx += n

        changes = 0

        # Bottom row cells (except the counter) must point Right.
        for j in range(m - 1):
            if grid[n - 1][j] == 'D':
                changes += 1

        # Rightmost column cells (except the counter) must point Down.
        for i in range(n - 1):
            if grid[i][m - 1] == 'R':
                changes += 1

        answers.append(str(changes))

    print("\n".join(answers))


if __name__ == "__main__":
    solve()