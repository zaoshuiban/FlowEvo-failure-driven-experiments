import sys

def main():
    input = sys.stdin.readline

    N = int(input())
    A = [list(input().strip()) for _ in range(N)]
    B = [row[:] for row in A]

    order = []

    # Top row: left to right
    for j in range(N):
        order.append((0, j))

    # Right column: top to bottom, excluding top-right
    for i in range(1, N):
        order.append((i, N - 1))

    # Bottom row: right to left, excluding bottom-right
    for j in range(N - 2, -1, -1):
        order.append((N - 1, j))

    # Left column: bottom to top, excluding both corners
    for i in range(N - 2, 0, -1):
        order.append((i, 0))

    values = [A[i][j] for i, j in order]
    L = len(values)

    for k, (i, j) in enumerate(order):
        B[i][j] = values[(k - 1) % L]

    for row in B:
        print("".join(row))

if __name__ == "__main__":
    main()