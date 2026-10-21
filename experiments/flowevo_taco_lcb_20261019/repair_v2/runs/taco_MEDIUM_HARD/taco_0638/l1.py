import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n, k = data[idx], data[idx + 1]
        idx += 2

        grid = [['0'] * n for _ in range(n)]

        for x in range(k):
            row = x % n
            col = (x // n + x % n) % n
            grid[row][col] = '1'

        min_f = 0 if k % n == 0 else 2
        output.append(str(min_f))

        for row in grid:
            output.append(''.join(row))

    sys.stdout.write('\n'.join(output))


if __name__ == "__main__":
    solve()