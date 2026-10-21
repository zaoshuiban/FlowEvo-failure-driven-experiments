import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])

    poland = set(data[2:2 + n])
    enemy = set(data[2 + n:2 + n + m])

    common = len(poland & enemy)

    poland_only = n - common
    enemy_only = m - common

    poland_score = poland_only + (common + 1) // 2
    enemy_score = enemy_only + common // 2

    print("YES" if poland_score > enemy_score else "NO")


if __name__ == "__main__":
    solve()