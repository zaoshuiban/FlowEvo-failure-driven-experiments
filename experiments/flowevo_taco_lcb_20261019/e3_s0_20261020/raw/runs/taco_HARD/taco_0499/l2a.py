import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    idx = 3
    win = False

    for _ in range(k):
        x, y = data[idx], data[idx + 1]
        idx += 2

        dist = min(x - 1, n - x, y - 1, m - y)
        if dist <= 4:
            win = True

    print("YES" if win else "NO")


if __name__ == "__main__":
    solve()