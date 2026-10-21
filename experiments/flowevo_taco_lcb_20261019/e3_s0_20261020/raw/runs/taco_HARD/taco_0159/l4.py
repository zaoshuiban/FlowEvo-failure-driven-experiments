import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    cnt = [0] * 4  # parity classes of (x/2, y/2)

    idx = 1
    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        px = (x >> 1) & 1
        py = (y >> 1) & 1
        cnt[px * 2 + py] += 1

    total = n * (n - 1) * (n - 2) // 6

    # A triangle is NOT interesting exactly when its three vertices
    # belong to three different parity classes.
    bad = 0
    for i in range(4):
        for j in range(i + 1, 4):
            for k in range(j + 1, 4):
                bad += cnt[i] * cnt[j] * cnt[k]

    print(total - bad)


if __name__ == "__main__":
    solve()