import sys


def solve() -> None:
    input = sys.stdin.readline

    N, M = map(int, input().split())

    # rows[v] is the coefficient row of the equation for vertex v.
    # Bit u is 1 iff u is adjacent to v.
    rows = [0] * N
    for _ in range(M):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        rows[u] |= 1 << v
        rows[v] |= 1 << u

    # Compute an RREF basis of the row space.
    mat = rows[:]
    pivot_cols = []
    rank = 0

    for col in range(N):
        pivot = -1
        for i in range(rank, N):
            if (mat[i] >> col) & 1:
                pivot = i
                break

        if pivot == -1:
            continue

        mat[rank], mat[pivot] = mat[pivot], mat[rank]

        for i in range(N):
            if i != rank and ((mat[i] >> col) & 1):
                mat[i] ^= mat[rank]

        pivot_cols.append(col)
        rank += 1

        if rank == N:
            break

    pivot_set = set(pivot_cols)

    # Construct a basis of the nullspace ker(A).
    basis = []
    for free_col in range(N):
        if free_col in pivot_set:
            continue

        vec = 1 << free_col

        for k, pivot_col in enumerate(pivot_cols):
            if (mat[k] >> free_col) & 1:
                vec |= 1 << pivot_col

        basis.append(vec)

    # A vertex can have a non-zero label iff its coordinate is 1
    # in at least one nullspace basis vector.
    union = 0
    for vec in basis:
        union |= vec

    for v in range(N):
        if ((union >> v) & 1) == 0:
            print("No")
            return

    # Use each basis vector as one bit-plane.
    ans = [0] * N
    for bit, vec in enumerate(basis):
        for v in range(N):
            if (vec >> v) & 1:
                ans[v] |= 1 << bit

    print("Yes")
    print(*ans)


if __name__ == "__main__":
    solve()