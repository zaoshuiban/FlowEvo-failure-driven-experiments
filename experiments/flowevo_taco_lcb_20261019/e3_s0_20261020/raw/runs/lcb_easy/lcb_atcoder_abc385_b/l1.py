import sys

def main():
    data = sys.stdin.buffer.read().split()
    H = int(data[0])
    W = int(data[1])
    X = int(data[2]) - 1
    Y = int(data[3]) - 1

    grid = data[4:4 + H]
    T = data[4 + H]

    x, y = X, Y
    visited_houses = set()

    for move in T:
        nx, ny = x, y

        if move == ord('U'):
            nx -= 1
        elif move == ord('D'):
            nx += 1
        elif move == ord('L'):
            ny -= 1
        elif move == ord('R'):
            ny += 1

        if 0 <= nx < H and 0 <= ny < W and grid[nx][ny] != ord('#'):
            x, y = nx, ny

        if grid[x][y] == ord('@'):
            visited_houses.add((x, y))

    print(x + 1, y + 1, len(visited_houses))

if __name__ == "__main__":
    main()