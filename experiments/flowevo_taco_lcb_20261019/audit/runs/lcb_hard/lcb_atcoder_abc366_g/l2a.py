import sys


def main():
    input = sys.stdin.buffer.readline

    N, M = map(int, input().split())
    rows = [0] * N

    for _ in range(M):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        rows[u] |= 1 << v
        rows[v] |= 1 << u

    a = rows[:]
    rank = 0
    pivots = []

    # Gauss-Jordan elimination over GF(2)
    for col in range(N):
        pivot = -1
        for i in range(rank, N):
            if (a[i] >> col) & 1:
                pivot = i
                break

        if pivot == -1:
            continue

        a[rank], a[pivot] = a[pivot], a[rank]

        for i in range(N):
            if i != rank and ((a[i] >> col) & 1):
                a[i] ^= a[rank]

        pivots.append(col)
        rank += 1

    is_pivot = [False] * N
    for col in pivots:
        is_pivot[col] = True

    # Build a basis of the nullspace of the adjacency matrix over GF(2).
    basis = []
    for free_col in range(N):
        if is_pivot[free_col]:
            continue

        vec = 1 << free_col
        for i, pivot_col in enumerate(pivots):
            if (a[i] >> free_col) & 1:
                vec |= 1 << pivot_col

        basis.append(vec)

    covered = 0
    for vec in basis:
        covered |= vec

    full_mask = (1 << N) - 1
    if covered != full_mask:
        print("No")
        return

    # For each vertex i, choose a nullspace vector whose i-th bit is 1.
    chosen = [0] * N
    for i in range(N):
        for vec in basis:
            if (vec >> i) & 1:
                chosen[i] = vec
                break

    answer = [0] * N

    # Use bit i for the vector chosen for vertex i.
    for i, vec in enumerate(chosen):
        bit_value = 1 << i
        for j in range(N):
            if (vec >> j) & 1:
                answer[j] |= bit_value

    print("Yes")
    print(*answer)


if __name__ == "__main__":
    main()