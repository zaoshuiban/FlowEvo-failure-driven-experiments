import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        grid = data[idx:idx + n]
        idx += n

        possible = True

        for i in range(n - 1):
            row = grid[i]
            next_row = grid[i + 1]

            for j in range(n - 1):
                if row[j] == ord('1') and row[j + 1] == ord('0') and next_row[j] == ord('0'):
                    possible = False
                    break

            if not possible:
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()