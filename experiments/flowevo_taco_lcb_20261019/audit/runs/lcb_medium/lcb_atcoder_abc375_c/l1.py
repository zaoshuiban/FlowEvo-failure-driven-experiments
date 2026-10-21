import sys

def main():
    input = sys.stdin.buffer.readline

    n = int(input())
    A = [input().strip() for _ in range(n)]

    n1 = n - 1
    half = n // 2

    # kseqs[a][c] = number of 90-degree counterclockwise rotations
    # needed for cell (r, c), where a = min(r, n - 1 - r).
    kseqs = []
    for a in range(half):
        arr = bytearray(n)
        for c in range(n):
            m = c if c < n1 - c else n1 - c
            layer_min = a if a < m else m
            arr[c] = (layer_min + 1) & 3
        kseqs.append(bytes(arr))

    answer = []

    for r in range(n):
        a = r if r < n1 - r else n1 - r
        ks = kseqs[a]

        row = bytearray(n)
        source_row = A[r]
        opposite_row = A[n1 - r]
        opposite_col = n1 - r

        for c in range(n):
            k = ks[c]

            if k == 0:
                row[c] = source_row[c]
            elif k == 1:
                row[c] = A[n1 - c][r]
            elif k == 2:
                row[c] = opposite_row[n1 - c]
            else:
                row[c] = A[c][opposite_col]

        answer.append(bytes(row))

    sys.stdout.buffer.write(b'\n'.join(answer))


if __name__ == "__main__":
    main()