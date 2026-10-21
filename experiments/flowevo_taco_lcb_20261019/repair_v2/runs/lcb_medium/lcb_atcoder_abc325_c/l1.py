import sys


def main():
    input = sys.stdin.buffer.readline
    H, W = map(int, input().split())

    stride = W + 2
    grid = bytearray(b'.' * ((H + 2) * stride))

    for i in range(1, H + 1):
        row = input().strip()
        start = i * stride + 1
        grid[start:start + W] = row

    offsets = (
        -stride - 1, -stride, -stride + 1,
        -1, 1,
        stride - 1, stride, stride + 1
    )

    SENSOR = ord('#')
    EMPTY = ord('.')
    answer = 0

    for i in range(1, H + 1):
        base = i * stride
        for j in range(1, W + 1):
            pos = base + j
            if grid[pos] != SENSOR:
                continue

            answer += 1
            grid[pos] = EMPTY
            stack = [pos]

            while stack:
                cur = stack.pop()
                for d in offsets:
                    nxt = cur + d
                    if grid[nxt] == SENSOR:
                        grid[nxt] = EMPTY
                        stack.append(nxt)

    print(answer)


if __name__ == "__main__":
    main()