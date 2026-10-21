import sys


def solve():
    input = sys.stdin.buffer.readline

    H, W = map(int, input().split())
    grid = [input().strip() for _ in range(H)]

    row_cnt = [[0] * 26 for _ in range(H)]
    col_cnt = [[0] * 26 for _ in range(W)]

    for i in range(H):
        line = grid[i]
        rc = row_cnt[i]
        for j, ch in enumerate(line):
            k = ch - ord('a')
            rc[k] += 1
            col_cnt[j][k] += 1

    row_distinct = [0] * H
    for i in range(H):
        row_distinct[i] = sum(1 for x in row_cnt[i] if x > 0)

    col_distinct = [0] * W
    for j in range(W):
        col_distinct[j] = sum(1 for x in col_cnt[j] if x > 0)

    active_row = [True] * H
    active_col = [True] * W

    row_queued = [False] * H
    col_queued = [False] * W

    row_q = []
    col_q = []

    active_rows_num = H
    active_cols_num = W

    if active_cols_num >= 2:
        for r in range(H):
            if row_distinct[r] == 1:
                row_q.append(r)
                row_queued[r] = True

    if active_rows_num >= 2:
        for c in range(W):
            if col_distinct[c] == 1:
                col_q.append(c)
                col_queued[c] = True

    while row_q or col_q:
        remove_rows = row_q
        remove_cols = col_q
        row_q = []
        col_q = []

        for r in remove_rows:
            if active_row[r]:
                active_row[r] = False
                active_rows_num -= 1

        for c in remove_cols:
            if active_col[c]:
                active_col[c] = False
                active_cols_num -= 1

        # Remove marked rows and update remaining active columns.
        for r in remove_rows:
            line = grid[r]
            for c in range(W):
                if active_col[c]:
                    k = line[c] - ord('a')
                    cnt = col_cnt[c]
                    cnt[k] -= 1

                    if cnt[k] == 0:
                        col_distinct[c] -= 1

                    if (
                        col_distinct[c] == 1
                        and active_rows_num >= 2
                        and not col_queued[c]
                    ):
                        col_queued[c] = True
                        col_q.append(c)

        # Remove marked columns and update remaining active rows.
        for c in remove_cols:
            for r in range(H):
                if active_row[r]:
                    k = grid[r][c] - ord('a')
                    cnt = row_cnt[r]
                    cnt[k] -= 1

                    if cnt[k] == 0:
                        row_distinct[r] -= 1

                    if (
                        row_distinct[r] == 1
                        and active_cols_num >= 2
                        and not row_queued[r]
                    ):
                        row_queued[r] = True
                        row_q.append(r)

    print(active_rows_num * active_cols_num)


if __name__ == "__main__":
    solve()