import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    A = data[1:1 + n]
    nm1 = n - 1

    result = []

    for r in range(n):
        row = bytearray(n)

        dr = min(r + 1, n - r)

        # Left edge: c = 0 ... dr - 1
        for c in range(dr):
            k = (c + 1) & 3
            if k == 0:
                row[c] = A[r][c]
            elif k == 1:
                row[c] = A[nm1 - c][r]
            elif k == 2:
                row[c] = A[nm1 - r][nm1 - c]
            else:
                row[c] = A[c][nm1 - r]

        lo = dr
        hi = n - dr

        # Middle part: layer = dr, so k is constant
        if lo < hi:
            k = dr & 3
            if k == 0:
                row[lo:hi] = A[r][lo:hi]
            elif k == 1:
                for c in range(lo, hi):
                    row[c] = A[nm1 - c][r]
            elif k == 2:
                row[lo:hi] = A[nm1 - r][lo:hi][::-1]
            else:
                for c in range(lo, hi):
                    row[c] = A[c][nm1 - r]

        # Right edge: c = hi ... n - 1
        for j in range(dr):
            c = hi + j
            k = (dr - j) & 3

            if k == 0:
                row[c] = A[r][c]
            elif k == 1:
                row[c] = A[nm1 - c][r]
            elif k == 2:
                row[c] = A[nm1 - r][nm1 - c]
            else:
                row[c] = A[c][nm1 - r]

        result.append(bytes(row))

    sys.stdout.buffer.write(b"\n".join(result))


if __name__ == "__main__":
    main()