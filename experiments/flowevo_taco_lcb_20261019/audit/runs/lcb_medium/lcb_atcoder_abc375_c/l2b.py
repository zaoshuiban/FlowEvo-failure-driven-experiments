import sys

def solve():
    input = sys.stdin.buffer.readline

    N = int(input())
    A = [input().strip() for _ in range(N)]

    n1 = N - 1
    h = [j if j < n1 - j else n1 - j for j in range(N)]

    result = []
    append = result.append

    for i in range(N):
        vi = i if i < n1 - i else n1 - i
        ri2 = n1 - i

        row = bytearray(N)
        Ai = A[i]

        for j in range(N):
            hj = h[j]
            d = vi if vi < hj else hj
            k = (d + 1) & 3

            if k == 0:
                row[j] = Ai[j]
            elif k == 1:
                row[j] = A[n1 - j][i]
            elif k == 2:
                row[j] = A[ri2][n1 - j]
            else:
                row[j] = A[j][ri2]

        append(bytes(row))

    sys.stdout.buffer.write(b"\n".join(result))

if __name__ == "__main__":
    solve()