import sys

def solve():
    data = sys.stdin.buffer
    first = data.readline()
    if not first:
        return

    n = int(first)

    # Number of bits needed so that all indices 0..n-1 have distinct codes.
    B = (n - 1).bit_length()

    res0 = [[0] * n for _ in range(B)]
    res1 = [[0] * n for _ in range(B)]

    out = sys.stdout

    def read_n_ints(cnt):
        vals = []
        while len(vals) < cnt:
            line = data.readline()
            if not line:
                break
            vals.extend(map(int, line.split()))
        return vals

    for b in range(B):
        # Query columns whose b-th bit is 0.
        cols0 = [str(i + 1) for i in range(n) if ((i >> b) & 1) == 0]
        out.write(str(len(cols0)) + "\n")
        out.write(" ".join(cols0) + "\n")
        out.flush()
        res0[b] = read_n_ints(n)

        # Query columns whose b-th bit is 1.
        cols1 = [str(i + 1) for i in range(n) if ((i >> b) & 1) == 1]
        out.write(str(len(cols1)) + "\n")
        out.write(" ".join(cols1) + "\n")
        out.flush()
        res1[b] = read_n_ints(n)

    answer = []

    for i in range(n):
        best = 10**18

        for b in range(B):
            # To exclude column i, for each bit take columns with the opposite bit.
            if (i >> b) & 1:
                value = res0[b][i]
            else:
                value = res1[b][i]

            if value < best:
                best = value

        answer.append(best)

    out.write("-1\n")
    out.write(" ".join(map(str, answer)) + "\n")
    out.flush()


if __name__ == "__main__":
    solve()