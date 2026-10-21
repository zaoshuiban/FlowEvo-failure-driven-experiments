import sys


def construct(n: int):
    # If n is a power of two, use the standard binary-reflected Gray code.
    if (n & (n - 1)) == 0:
        res = [0] * n
        for i in range(n):
            res[i] = i ^ (i >> 1)
        return res

    m = 1 << (n.bit_length() - 1)  # largest power of two <= n
    r = n - m

    high_part_base = construct(r)
    bridge_vertex = high_part_base[-1]

    res = [m + x for x in high_part_base]

    # Hamilton path of the full m-vertex hypercube starting at bridge_vertex.
    append = res.append
    for i in range(m):
        gray = i ^ (i >> 1)
        append(gray ^ bridge_vertex)

    return res


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        ans = construct(n)
        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()