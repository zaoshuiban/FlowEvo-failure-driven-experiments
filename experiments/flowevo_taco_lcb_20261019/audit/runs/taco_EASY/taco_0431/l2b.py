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

    if n > m:
        print("YES")
    elif n < m:
        print("NO")
    else:
        print("YES" if common % 2 == 1 else "NO")

if __name__ == "__main__":
    solve()