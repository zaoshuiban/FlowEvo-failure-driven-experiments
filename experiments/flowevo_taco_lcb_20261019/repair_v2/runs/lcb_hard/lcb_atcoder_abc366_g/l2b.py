import sys


def main():
    input = sys.stdin.readline

    N, M = map(int, input().split())
    adj = [0] * N

    for _ in range(M):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        adj[u] |= 1 << v
        adj[v] |= 1 << u

    coeff_mask = (1 << N) - 1
    solutions = []

    for b in range(N):
        # Equations: A * z = 0, and z_b = 1.
        # Variable bits are 0..N-1. RHS is stored at bit N.
        rows = adj[:]
        rows.append((1 << b) | (1 << N))

        rank = 0
        pivots = []

        for col in range(N):
            pivot = -1
            for r in range(rank, N + 1):
                if (rows[r] >> col) & 1:
                    pivot = r
                    break

            if pivot == -1:
                continue

            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            pivot_row = rows[rank]

            for r in range(N + 1):
                if r != rank and ((rows[r] >> col) & 1):
                    rows[r] ^= pivot_row

            pivots.append(col)
            rank += 1

        possible = True
        for r in range(rank, N + 1):
            if (rows[r] & coeff_mask) == 0 and ((rows[r] >> N) & 1):
                possible = False
                break

        if not possible:
            print("No")
            return

        sol = 0
        for i, col in enumerate(pivots):
            if (rows[i] >> N) & 1:
                sol |= 1 << col

        solutions.append(sol)

    ans = [0] * N

    for b, z in enumerate(solutions):
        for v in range(N):
            if (z >> v) & 1:
                ans[v] |= 1 << b

    print("Yes")
    print(*ans)


if __name__ == "__main__":
    main()