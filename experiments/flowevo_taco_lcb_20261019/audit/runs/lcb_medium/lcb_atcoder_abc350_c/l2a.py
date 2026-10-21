import sys

def solve():
    input = sys.stdin.readline
    N = int(input())
    A = list(map(int, input().split()))

    pos = [0] * (N + 1)
    for i, value in enumerate(A):
        pos[value] = i

    operations = []

    for i in range(N):
        target = i + 1
        if A[i] != target:
            j = pos[target]
            old = A[i]

            A[i], A[j] = A[j], A[i]
            pos[target] = i
            pos[old] = j

            operations.append((i + 1, j + 1))

    out = [str(len(operations))]
    for i, j in operations:
        out.append(f"{i} {j}")

    print("\n".join(out))

if __name__ == "__main__":
    solve()