import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    P = data[1:1 + N]
    Q = data[1 + N:1 + 2 * N]

    posP = [0] * (N + 1)
    posQ = [0] * (N + 1)

    for idx, row in enumerate(P):
        posP[row] = idx

    for idx, col in enumerate(Q):
        posQ[col] = idx

    ans = []
    threshold = N - 1

    for i in range(1, N + 1):
        row_chars = []
        for j in range(1, N + 1):
            if posP[i] + posQ[j] >= threshold:
                row_chars.append('1')
            else:
                row_chars.append('0')
        ans.append(''.join(row_chars))

    sys.stdout.write('\n'.join(ans))

if __name__ == "__main__":
    main()