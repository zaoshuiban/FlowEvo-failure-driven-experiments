import sys

def solve():
    input = sys.stdin.buffer.readline

    H, W = map(int, input().split())
    grid = [bytearray(input().strip()) for _ in range(H)]

    HASH = ord('#')
    DOT = ord('.')

    ans = 0
    stack = []

    for i in range(H):
        row = grid[i]
        for j in range(W):
            if row[j] != HASH:
                continue

            ans += 1
            row[j] = DOT
            stack.append(i * W + j)

            while stack:
                v = stack.pop()
                x = v // W
                y = v - x * W

                start_x = max(0, x - 1)
                end_x = min(H, x + 2)
                start_y = max(0, y - 1)
                end_y = min(W, y + 2)

                for nx in range(start_x, end_x):
                    r = grid[nx]
                    for ny in range(start_y, end_y):
                        if r[ny] == HASH:
                            r[ny] = DOT
                            stack.append(nx * W + ny)

    print(ans)


if __name__ == "__main__":
    solve()