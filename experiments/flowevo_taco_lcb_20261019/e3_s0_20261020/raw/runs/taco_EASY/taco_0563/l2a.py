import sys

def solve():
    input = sys.stdin.readline
    t = int(input())
    results = []

    for _ in range(t):
        n, m = map(int, input().split())
        grid = [input().strip() for _ in range(n)]

        changes = 0

        # Last column, except the counter cell, must all point down.
        for i in range(n - 1):
            if grid[i][m - 1] == 'R':
                changes += 1

        # Last row, except the counter cell, must all point right.
        for j in range(m - 1):
            if grid[n - 1][j] == 'D':
                changes += 1

        results.append(str(changes))

    sys.stdout.write("\n".join(results))


if __name__ == "__main__":
    solve()