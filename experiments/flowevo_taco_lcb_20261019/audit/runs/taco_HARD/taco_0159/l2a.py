import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    cnt = [0, 0, 0, 0]

    idx = 1
    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        px = (x >> 1) & 1
        py = (y >> 1) & 1
        cnt[(px << 1) | py] += 1

    c0, c1, c2, c3 = cnt

    total = n * (n - 1) * (n - 2) // 6

    bad = (
        c0 * c1 * c2
        + c0 * c1 * c3
        + c0 * c2 * c3
        + c1 * c2 * c3
    )

    print(total - bad)


if __name__ == "__main__":
    main()