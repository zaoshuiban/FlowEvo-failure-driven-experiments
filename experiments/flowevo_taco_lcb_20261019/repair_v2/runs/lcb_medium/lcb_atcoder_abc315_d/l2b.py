import sys


def main():
    data = sys.stdin.buffer.read().split()
    H = int(data[0])
    W = int(data[1])
    grid = data[2:2 + H]

    row_counts = [[0] * 26 for _ in range(H)]
    col_counts = [[0] * 26 for _ in range(W)]

    for i in range(H):
        row = grid[i]
        rc = row_counts[i]
        for j, ch in enumerate(row):
            color = ch - 97
            rc[color] += 1
            col_counts[j][color] += 1

    row_distinct = [0] * H
    for i in range(H):
        row_distinct[i] = sum(1 for x in row_counts[i] if x > 0)

    col_distinct = [0] * W
    for j in range(W):
        col_distinct[j] = sum(1 for x in col_counts[j] if x > 0)

    active_row = [True] * H
    active_col = [True] * W
    active_rows = H
    active_cols = W

    while True:
        delete_rows = []
        if active_cols >= 2:
            for r in range(H):
                if active_row[r] and row_distinct[r] == 1:
                    delete_rows.append(r)

        delete_cols = []
        if active_rows >= 2:
            for c in range(W):
                if active_col[c] and col_distinct[c] == 1:
                    delete_cols.append(c)

        if not delete_rows and not delete_cols:
            break

        for r in delete_rows:
            row = grid[r]
            for c in range(W):
                if active_col[c]:
                    color = row[c] - 97
                    col_counts[c][color] -= 1
                    if col_counts[c][color] == 0:
                        col_distinct[c] -= 1

        for r in delete_rows:
            active_row[r] = False
        active_rows -= len(delete_rows)

        for c in delete_cols:
            for r in range(H):
                if active_row[r]:
                    color = grid[r][c] - 97
                    row_counts[r][color] -= 1
                    if row_counts[r][color] == 0:
                        row_distinct[r] -= 1

        for c in delete_cols:
            active_col[c] = False
        active_cols -= len(delete_cols)

    print(active_rows * active_cols)


if __name__ == "__main__":
    main()