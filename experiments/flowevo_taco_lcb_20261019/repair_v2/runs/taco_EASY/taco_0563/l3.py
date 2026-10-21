import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
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

        # Cells on the bottom row except the counter must point Right.
        last_row = grid[n - 1]
        for j in range(m - 1):
            if last_row[j] == ord('D'):
                changes += 1

        # Cells on the rightmost column except the counter must point Down.
        for i in range(n - 1):
            if grid[i][m - 1] == ord('R'):
                changes += 1

        answers.append(str(changes))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()