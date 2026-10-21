import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    P = data[1:1 + N]
    Q = data[1 + N:1 + 2 * N]

    rank_row = [0] * (N + 1)
    rank_col = [0] * (N + 1)

    for pos, row in enumerate(P, 1):
        rank_row[row] = pos

    for pos, col in enumerate(Q, 1):
        rank_col[col] = pos

    ans = []
    for i in range(1, N + 1):
        threshold = N - rank_row[i]
        line = ''.join(
            '1' if rank_col[j] > threshold else '0'
            for j in range(1, N + 1)
        )
        ans.append(line)

    sys.stdout.write('\n'.join(ans))

if __name__ == "__main__":
    main()