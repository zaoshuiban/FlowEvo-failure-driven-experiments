import sys


def solve() -> None:
    input = sys.stdin.buffer.readline

    H, W = map(int, input().split())

    grid = []
    row_freq = [[0] * 26 for _ in range(H)]
    col_freq = [[0] * 26 for _ in range(W)]
    row_distinct = [0] * H
    col_distinct = [0] * W

    for i in range(H):
        row = input().strip()
        grid.append(row)
        rf = row_freq[i]

        for j, ch in enumerate(row):
            x = ch - 97

            if rf[x] == 0:
                row_distinct[i] += 1
            rf[x] += 1

            cf = col_freq[j]
            if cf[x] == 0:
                col_distinct[j] += 1
            cf[x] += 1

    row_total = [W] * H
    col_total = [H] * W

    row_active = [True] * H
    col_active = [True] * W

    rem_rows = [
        i for i in range(H)
        if row_total[i] >= 2 and row_distinct[i] == 1
    ]
    rem_cols = [
        j for j in range(W)
        if col_total[j] >= 2 and col_distinct[j] == 1
    ]

    active_rows = H
    active_cols = W

    while rem_rows or rem_cols:
        for i in rem_rows:
            row_active[i] = False
        active_rows -= len(rem_rows)

        for j in rem_cols:
            col_active[j] = False
        active_cols -= len(rem_cols)

        # Remove marked columns from the remaining rows.
        for j in rem_cols:
            for i in range(H):
                if row_active[i]:
                    x = grid[i][j] - 97
                    row_total[i] -= 1

                    f = row_freq[i][x] - 1
                    row_freq[i][x] = f
                    if f == 0:
                        row_distinct[i] -= 1

        # Remove marked rows from the remaining columns.
        for i in rem_rows:
            gi = grid[i]
            for j in range(W):
                if col_active[j]:
                    x = gi[j] - 97
                    col_total[j] -= 1

                    f = col_freq[j][x] - 1
                    col_freq[j][x] = f
                    if f == 0:
                        col_distinct[j] -= 1

        next_rows = []
        for i in range(H):
            if row_active[i] and row_total[i] >= 2 and row_distinct[i] == 1:
                next_rows.append(i)

        next_cols = []
        for j in range(W):
            if col_active[j] and col_total[j] >= 2 and col_distinct[j] == 1:
                next_cols.append(j)

        rem_rows, rem_cols = next_rows, next_cols

    print(active_rows * active_cols)


if __name__ == "__main__":
    solve()