import sys


def construct(n: int):
    # A single vertex
    if n == 1:
        return [0]

    # If n is a power of two, the standard binary-reflected Gray code works.
    if (n & (n - 1)) == 0:
        return [i ^ (i >> 1) for i in range(n)]

    m = 1 << (n.bit_length() - 1)  # largest power of two <= n
    r = n - m

    # Construct a valid path for [0, r - 1].
    p = construct(r)
    bridge = p[-1]

    # Put vertices [m, n - 1] first by adding m to every vertex of p.
    ans = [m + x for x in p]

    # Then visit all vertices [0, m - 1] using a Gray code
    # translated so that it starts at bridge.
    ans.extend(((i ^ (i >> 1)) ^ bridge for i in range(m)))

    return ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    out = []

    for i in range(1, t + 1):
        n = data[i]
        ans = construct(n)
        out.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()