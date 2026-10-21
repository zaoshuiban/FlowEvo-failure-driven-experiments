import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    counts = data[1:1 + n]

    ans = 0
    free = 0

    for c in counts:
        triangles = min(c // 2, (c + free) // 3)
        ans += triangles
        free = c + free - 3 * triangles

    print(ans)

if __name__ == "__main__":
    solve()