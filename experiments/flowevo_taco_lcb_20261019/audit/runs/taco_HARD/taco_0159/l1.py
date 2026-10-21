import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    cnt = [0, 0, 0, 0]
    pos = 1
    for _ in range(n):
        x = data[pos]
        y = data[pos + 1]
        pos += 2

        # Work with half-coordinates. Their parities are determined by x mod 4, y mod 4.
        px = (x // 2) & 1
        py = (y // 2) & 1
        cnt[px | (py << 1)] += 1

    total = n * (n - 1) * (n - 2) // 6

    bad = (
        cnt[0] * cnt[1] * cnt[2]
        + cnt[0] * cnt[1] * cnt[3]
        + cnt[0] * cnt[2] * cnt[3]
        + cnt[1] * cnt[2] * cnt[3]
    )

    print(total - bad)

if __name__ == "__main__":
    main()