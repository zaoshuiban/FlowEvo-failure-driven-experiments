import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    ax, ay = data[1], data[2]
    bx, by = data[3], data[4]
    cx, cy = data[5], data[6]

    same_side_row = (bx < ax) == (cx < ax)
    same_side_col = (by < ay) == (cy < ay)

    print("YES" if same_side_row and same_side_col else "NO")

if __name__ == "__main__":
    solve()