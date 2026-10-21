import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    degrees = data[1:1 + n]

    if n == 1:
        # A single-vertex tree has degree 0.
        print("Yes" if degrees and degrees[0] == 0 else "No")
        return

    if sum(degrees) == 2 * (n - 1) and all(d > 0 for d in degrees):
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()