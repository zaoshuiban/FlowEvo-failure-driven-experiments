import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    P = [x - 1 for x in data[1:1 + n]]
    Q = [x - 1 for x in data[1 + n:1 + 2 * n]]

    posP = [0] * n
    posQ = [0] * n

    for i, x in enumerate(P):
        posP[x] = i
    for i, x in enumerate(Q):
        posQ[x] = i

    ans = []
    for i in range(n):
        row = []
        pi = posP[i]
        for j in range(n):
            if pi + posQ[j] >= n - 1:
                row.append('1')
            else:
                row.append('0')
        ans.append(''.join(row))

    sys.stdout.write('\n'.join(ans) + '\n')

if __name__ == "__main__":
    main()