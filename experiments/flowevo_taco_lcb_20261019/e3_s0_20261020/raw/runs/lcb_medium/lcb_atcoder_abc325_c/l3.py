import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    H = int(data[0])
    W = int(data[1])
    rows = data[2:2 + H]

    Wp = W + 2
    Np = (H + 2) * Wp

    # 1 means a sensor, 0 means empty or already visited.
    grid = bytearray(Np)

    for i, row in enumerate(rows):
        base = (i + 1) * Wp + 1
        for j, c in enumerate(row):
            if c == ord('#'):
                grid[base + j] = 1

    directions = (
        -Wp - 1, -Wp, -Wp + 1,
        -1,              1,
        Wp - 1,  Wp,  Wp + 1
    )

    answer = 0

    for i in range(1, H + 1):
        base = i * Wp + 1
        for start in range(base, base + W):
            if grid[start] == 0:
                continue

            answer += 1
            grid[start] = 0
            stack = [start]

            while stack:
                pos = stack.pop()

                for d in directions:
                    nxt = pos + d
                    if grid[nxt]:
                        grid[nxt] = 0
                        stack.append(nxt)

    print(answer)


if __name__ == "__main__":
    main()