import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    M = int(data[1])

    adj = [0] * N
    idx = 2
    for _ in range(M):
        u = int(data[idx]) - 1
        v = int(data[idx + 1]) - 1
        idx += 2
        adj[u] |= 1 << v
        adj[v] |= 1 << u

    # Gaussian elimination over GF(2) for the equations A * x = 0.
    rows = adj[:]
    pivot_cols = []
    rank = 0

    for col in range(N):
        pivot = -1
        for r in range(rank, N):
            if (rows[r] >> col) & 1:
                pivot = r
                break

        if pivot == -1:
            continue

        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        pivot_row = rows[rank]

        for r in range(N):
            if r != rank and ((rows[r] >> col) & 1):
                rows[r] ^= pivot_row

        pivot_cols.append(col)
        rank += 1

    is_pivot = [False] * N
    for c in pivot_cols:
        is_pivot[c] = True

    # Build a basis of the nullspace of A.
    basis = []
    for free_col in range(N):
        if is_pivot[free_col]:
            continue

        vec = 1 << free_col
        for i, pivot_col in enumerate(pivot_cols):
            if (rows[i] >> free_col) & 1:
                vec |= 1 << pivot_col

        basis.append(vec)

    # For each vertex v, choose a nullspace vector whose v-th coordinate is 1.
    witness = [0] * N
    for v in range(N):
        for vec in basis:
            if (vec >> v) & 1:
                witness[v] = vec
                break

        if witness[v] == 0:
            print("No")
            return

    ans = [0] * N

    # Assign bit v according to witness[v].
    for v in range(N):
        bit = 1 << v
        vec = witness[v]

        for x in range(N):
            if (vec >> x) & 1:
                ans[x] |= bit

    print("Yes")
    print(*ans)


if __name__ == "__main__":
    main()