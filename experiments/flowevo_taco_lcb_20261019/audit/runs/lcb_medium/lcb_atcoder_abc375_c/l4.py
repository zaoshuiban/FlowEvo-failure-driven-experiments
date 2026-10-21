import sys


def solve() -> None:
    data = sys.stdin.buffer
    N = int(data.readline())
    A = [data.readline().strip() for _ in range(N)]

    n1 = N - 1
    half = N // 2
    out = []

    for r in range(N):
        row = bytearray(N)
        nr = n1 - r
        base = r if r < nr else nr

        Ar = A[r]
        Anr = A[nr]

        for c in range(half):
            c2 = n1 - c

            # Layer distance from the border, considering this column pair.
            d = c if c < base else base
            k = (d + 1) & 3

            if k == 0:
                row[c] = Ar[c]
                row[c2] = Ar[c2]
            elif k == 1:
                row[c] = A[c2][r]
                row[c2] = A[c][r]
            elif k == 2:
                row[c] = Anr[c2]
                row[c2] = Anr[c]
            else:
                row[c] = A[c][nr]
                row[c2] = A[c2][nr]

        out.append(bytes(row))

    sys.stdout.buffer.write(b"\n".join(out))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    solve()