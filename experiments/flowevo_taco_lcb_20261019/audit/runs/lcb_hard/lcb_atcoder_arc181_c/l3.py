import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    P = data[1:1 + N]
    Q = data[1 + N:1 + 2 * N]

    posP = [0] * (N + 1)
    posQ = [0] * (N + 1)

    for idx, value in enumerate(P, start=1):
        posP[value] = idx

    for idx, value in enumerate(Q, start=1):
        posQ[value] = idx

    ans = []
    for i in range(1, N + 1):
        row = []
        pi = posP[i]
        for j in range(1, N + 1):
            if pi + posQ[j] > N:
                row.append('1')
            else:
                row.append('0')
        ans.append(''.join(row))

    sys.stdout.write('\n'.join(ans) + '\n')


if __name__ == "__main__":
    main()