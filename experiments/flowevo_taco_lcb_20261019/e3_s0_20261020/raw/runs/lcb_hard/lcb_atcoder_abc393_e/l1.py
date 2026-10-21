import sys
import math


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N = data[0]
    K = data[1]
    A = data[2:2 + N]
    del data

    write = sys.stdout.write

    if K == 1:
        chunk = []
        for x in A:
            chunk.append(str(x))
            if len(chunk) >= 10000:
                write("\n".join(chunk) + "\n")
                chunk.clear()
        if chunk:
            write("\n".join(chunk) + "\n")
        return

    if K == N:
        g = 0
        for x in A:
            g = math.gcd(g, x)
        write((str(g) + "\n") * N)
        return

    M = max(A)
    M1 = M + 1

    freq = [0] * M1
    for x in A:
        freq[x] += 1

    count = [0] * M1
    for d in range(1, M1):
        s = 0
        for multiple in range(d, M1, d):
            s += freq[multiple]
        count[d] = s

    best = [0] * M1
    for d in range(1, M1):
        if count[d] >= K:
            for multiple in range(d, M1, d):
                best[multiple] = d

    chunk = []
    for x in A:
        chunk.append(str(best[x]))
        if len(chunk) >= 10000:
            write("\n".join(chunk) + "\n")
            chunk.clear()

    if chunk:
        write("\n".join(chunk) + "\n")


if __name__ == "__main__":
    main()