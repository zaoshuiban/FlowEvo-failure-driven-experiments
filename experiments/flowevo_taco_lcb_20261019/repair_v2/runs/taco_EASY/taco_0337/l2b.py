import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        grid = [next(it) for _ in range(n)]

        possible = True

        for i in range(n - 1):
            for j in range(n - 1):
                if (
                    grid[i][j] == ord('1')
                    and grid[i][j + 1] == ord('0')
                    and grid[i + 1][j] == ord('0')
                ):
                    possible = False
                    break
            if not possible:
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()