import sys

def solve():
    input = sys.stdin.buffer.readline

    n, m = map(int, input().split())

    poland = set()
    for _ in range(n):
        poland.add(input().strip())

    common = 0
    for _ in range(m):
        word = input().strip()
        if word in poland:
            common += 1

    if common % 2 == 1:
        n += 1

    print("YES" if n > m else "NO")


if __name__ == "__main__":
    solve()