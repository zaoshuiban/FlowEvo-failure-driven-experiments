import sys

def solve():
    input = sys.stdin.readline
    t = int(input())
    answers = []

    for _ in range(t):
        n = int(input())
        grid = [input().strip() for _ in range(n)]

        valid = True

        for i in range(n):
            for j in range(n):
                if grid[i][j] == '1':
                    if i == n - 1 or j == n - 1:
                        continue
                    if grid[i + 1][j] != '1' and grid[i][j + 1] != '1':
                        valid = False
                        break
            if not valid:
                break

        answers.append("YES" if valid else "NO")

    print("\n".join(answers))

if __name__ == "__main__":
    solve()