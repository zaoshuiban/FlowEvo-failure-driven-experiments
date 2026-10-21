import sys

def solve():
    input = sys.stdin.readline
    t = int(input())
    answers = []

    for _ in range(t):
        n = int(input())
        grid = [input().strip() for _ in range(n)]

        valid = True
        for i in range(n - 1):
            for j in range(n - 1):
                if grid[i][j] == '1':
                    if grid[i + 1][j] != '1' and grid[i][j + 1] != '1':
                        valid = False
                        break
            if not valid:
                break

        answers.append("YES" if valid else "NO")

    print("\n".join(answers))

if __name__ == "__main__":
    solve()