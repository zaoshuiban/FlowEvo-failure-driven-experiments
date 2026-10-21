import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    idx = 0
    t = int(data[idx])
    idx += 1

    answers = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        grid = [data[idx + i].decode() for i in range(n)]
        idx += n

        changes = 0

        # Bottom row cells except the counter must point Right.
        for j in range(m - 1):
            if grid[n - 1][j] != 'R':
                changes += 1

        # Rightmost column cells except the counter must point Down.
        for i in range(n - 1):
            if grid[i][m - 1] != 'D':
                changes += 1

        answers.append(str(changes))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()