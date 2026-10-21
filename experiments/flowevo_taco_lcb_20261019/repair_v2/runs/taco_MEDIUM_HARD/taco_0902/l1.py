import sys

def solve() -> None:
    n, p = map(int, sys.stdin.buffer.readline().split())

    for k in range(1, 101):
        s = n - k * p

        if s < k:
            if p >= 0:
                break
            continue

        if s.bit_count() <= k:
            print(k)
            return

    print(-1)

if __name__ == "__main__":
    solve()