import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])

    poland_words = set(data[2:2 + n])
    enemy_words = data[2 + n:2 + n + m]

    common = sum(1 for word in enemy_words if word in poland_words)

    if n + (common % 2) > m:
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    solve()