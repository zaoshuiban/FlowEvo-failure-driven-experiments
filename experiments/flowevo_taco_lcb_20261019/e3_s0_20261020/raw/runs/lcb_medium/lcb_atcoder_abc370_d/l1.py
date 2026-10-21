import sys
from array import array


def main():
    input = sys.stdin.buffer.readline

    H, W, Q = map(int, input().split())
    remaining = H * W

    row_stride = W + 2
    col_stride = H + 2

    row_size = (H + 1) * row_stride
    col_size = (W + 1) * col_stride

    row_next = array('i', range(row_size))
    row_prev = array('i', range(row_size))
    col_next = array('i', range(col_size))
    col_prev = array('i', range(col_size))

    def find(parent, x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def remove_cell(r, c):
        nonlocal remaining
        remaining -= 1

        rb = r * row_stride
        idx = rb + c
        row_next[idx] = find(row_next, rb + c + 1)
        row_prev[idx] = find(row_prev, rb + c - 1)

        cb = c * col_stride
        idx2 = cb + r
        col_next[idx2] = find(col_next, cb + r + 1)
        col_prev[idx2] = find(col_prev, cb + r - 1)

    for _ in range(Q):
        r, c = map(int, input().split())

        rb = r * row_stride
        idx = rb + c

        if row_next[idx] == idx:
            remove_cell(r, c)
        else:
            candidates = []

            left = find(row_prev, idx)
            if left != rb:
                candidates.append((r, left - rb))

            right = find(row_next, idx)
            if right != rb + W + 1:
                candidates.append((r, right - rb))

            cb = c * col_stride
            idx2 = cb + r

            up = find(col_prev, idx2)
            if up != cb:
                candidates.append((up - cb, c))

            down = find(col_next, idx2)
            if down != cb + H + 1:
                candidates.append((down - cb, c))

            for rr, cc in candidates:
                remove_cell(rr, cc)

    print(remaining)


if __name__ == "__main__":
    main()