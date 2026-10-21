import sys


def solve() -> None:
    input = sys.stdin.buffer.readline

    N = int(input())
    A = [input().strip() for _ in range(N)]

    n1 = N - 1
    result = []

    for i in range(N):
        vi = i if i < n1 - i else n1 - i
        ri2 = n1 - i
        Ai = A[i]

        row = bytearray(N)

        left = vi
        right = n1 - vi  # inclusive

        kc = (vi + 1) & 3

        if kc == 0:
            row[left:right + 1] = Ai[left:right + 1]
        elif kc == 1:
            row[left:right + 1] = bytes(
                A[n1 - j][i] for j in range(left, right + 1)
            )
        elif kc == 2:
            a = n1 - right
            b = n1 - left
            row[left:right + 1] = A[ri2][a:b + 1][::-1]
        else:
            row[left:right + 1] = bytes(
                A[j][ri2] for j in range(left, right + 1)
            )

        for j in range(left):
            k = (j + 1) & 3
            if k == 0:
                row[j] = Ai[j]
            elif k == 1:
                row[j] = A[n1 - j][i]
            elif k == 2:
                row[j] = A[ri2][n1 - j]
            else:
                row[j] = A[j][ri2]

        for j in range(right + 1, N):
            k = (n1 - j + 1) & 3
            if k == 0:
                row[j] = Ai[j]
            elif k == 1:
                row[j] = A[n1 - j][i]
            elif k == 2:
                row[j] = A[ri2][n1 - j]
            else:
                row[j] = A[j][ri2]

        result.append(bytes(row))

    sys.stdout.buffer.write(b"\n".join(result))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    solve()