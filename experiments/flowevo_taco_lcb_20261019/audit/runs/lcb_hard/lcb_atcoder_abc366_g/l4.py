import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])

    adj = [0] * n
    idx = 2
    for _ in range(m):
        u = int(data[idx]) - 1
        v = int(data[idx + 1]) - 1
        idx += 2
        adj[u] |= 1 << v
        adj[v] |= 1 << u

    # Gaussian elimination over GF(2).
    mat = adj[:]
    pivots = []
    row = 0

    for col in range(n):
        pivot = -1
        for i in range(row, n):
            if (mat[i] >> col) & 1:
                pivot = i
                break

        if pivot == -1:
            continue

        mat[row], mat[pivot] = mat[pivot], mat[row]
        pivot_row = mat[row]

        for i in range(n):
            if i != row and ((mat[i] >> col) & 1):
                mat[i] ^= pivot_row

        pivots.append(col)
        row += 1

    # Build a basis of the nullspace of the adjacency matrix.
    is_pivot = [False] * n
    for col in pivots:
        is_pivot[col] = True

    basis = []
    for free_col in range(n):
        if is_pivot[free_col]:
            continue

        vec = 1 << free_col

        for i, pivot_col in enumerate(pivots):
            if (mat[i] >> free_col) & 1:
                vec |= 1 << pivot_col

        basis.append(vec)

    # Use each nullspace basis vector as one bit position.
    ans = [0] * n
    for bit_index, vec in enumerate(basis):
        bit = 1 << bit_index
        for v in range(n):
            if (vec >> v) & 1:
                ans[v] |= bit

    if any(x == 0 for x in ans):
        print("No")
    else:
        print("Yes")
        print(*ans)


if __name__ == "__main__":
    main()