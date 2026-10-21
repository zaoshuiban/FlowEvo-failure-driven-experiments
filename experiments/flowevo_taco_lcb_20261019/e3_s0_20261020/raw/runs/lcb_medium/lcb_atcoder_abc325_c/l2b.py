import sys

def main():
    input = sys.stdin.buffer.readline
    H, W = map(int, input().split())
    grid = [bytearray(input().strip()) for _ in range(H)]

    SENSOR = ord('#')
    VISITED = ord('.')

    directions = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    )

    answer = 0

    for i in range(H):
        for j in range(W):
            if grid[i][j] == SENSOR:
                answer += 1
                grid[i][j] = VISITED
                stack = [i * W + j]

                while stack:
                    pos = stack.pop()
                    x = pos // W
                    y = pos % W

                    for dx, dy in directions:
                        nx = x + dx
                        ny = y + dy

                        if 0 <= nx < H and 0 <= ny < W:
                            if grid[nx][ny] == SENSOR:
                                grid[nx][ny] = VISITED
                                stack.append(nx * W + ny)

    print(answer)


if __name__ == "__main__":
    main()