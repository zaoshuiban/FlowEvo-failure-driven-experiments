import sys
import math

def main():
    N, M = map(int, sys.stdin.buffer.readline().split())

    K = M - 10 * (N - 1)
    count = math.comb(N + K - 1, N)

    result = [str(count)]
    seq = [0] * N
    offsets = [10 * i for i in range(N)]

    def dfs(index, minimum):
        if index == N:
            result.append(" ".join(str(seq[i] + offsets[i]) for i in range(N)))
            return

        for value in range(minimum, K + 1):
            seq[index] = value
            dfs(index + 1, value)

    dfs(0, 1)

    sys.stdout.write("\n".join(result) + "\n")

if __name__ == "__main__":
    main()