import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a1, a2, a3 = data[1:4]
    b1, b2, b3 = data[4:7]

    max_wins = min(a1, b2) + min(a2, b3) + min(a3, b1)

    min_wins = max(
        0,
        a1 - (b1 + b3),
        a2 - (b2 + b1),
        a3 - (b3 + b2)
    )

    print(min_wins, max_wins)

if __name__ == "__main__":
    solve()