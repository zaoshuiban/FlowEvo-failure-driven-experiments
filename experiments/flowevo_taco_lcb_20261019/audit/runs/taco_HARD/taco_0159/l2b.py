import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    cnt = [0, 0, 0, 0]

    idx = 1
    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        parity_x = (x // 2) & 1
        parity_y = (y // 2) & 1
        cnt[parity_x * 2 + parity_y] += 1

    total = n * (n - 1) * (n - 2) // 6

    c0, c1, c2, c3 = cnt
    bad = (
        c0 * c1 * c2
        + c0 * c1 * c3
        + c0 * c2 * c3
        + c1 * c2 * c3
    )

    print(total - bad)

if __name__ == "__main__":
    main()