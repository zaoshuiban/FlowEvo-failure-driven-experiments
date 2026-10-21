import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M = data[0], data[1]

    rows_set = set()
    cols_set = set()
    sums_set = set()
    diffs_set = set()

    idx = 2
    for _ in range(M):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        rows_set.add(a)
        cols_set.add(b)
        sums_set.add(a + b)
        diffs_set.add(a - b)

    rows = list(rows_set)
    cols = list(cols_set)

    base = (N - len(rows_set)) * (N - len(cols_set))

    total_diagonal_cells = 0

    # Diagonals of the form i + j = s
    for s in sums_set:
        L = max(1, s - N)
        U = min(N, s - 1)

        if L > U:
            continue

        length = U - L + 1

        row_forbidden = 0
        overlap = 0

        for r in rows:
            if L <= r <= U:
                row_forbidden += 1
                if (s - r) in cols_set:
                    overlap += 1

        col_forbidden = 0
        for c in cols:
            i = s - c
            if L <= i <= U:
                col_forbidden += 1

        total_diagonal_cells += length - row_forbidden - col_forbidden + overlap

    # Diagonals of the form i - j = d
    for d in diffs_set:
        L = max(1, d + 1)
        U = min(N, N + d)

        if L > U:
            continue

        length = U - L + 1

        row_forbidden = 0
        overlap = 0

        for r in rows:
            if L <= r <= U:
                row_forbidden += 1
                if (r - d) in cols_set:
                    overlap += 1

        col_forbidden = 0
        for c in cols:
            i = c + d
            if L <= i <= U:
                col_forbidden += 1

        total_diagonal_cells += length - row_forbidden - col_forbidden + overlap

    # Intersections of selected i+j and i-j diagonals were counted twice.
    intersections = 0

    for s in sums_set:
        for d in diffs_set:
            sd = s + d
            if sd & 1:
                continue

            i = sd // 2
            j = (s - d) // 2

            if 1 <= i <= N and 1 <= j <= N:
                if i not in rows_set and j not in cols_set:
                    intersections += 1

    answer = base - total_diagonal_cells + intersections
    print(answer)


if __name__ == "__main__":
    main()