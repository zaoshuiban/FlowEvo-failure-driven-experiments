import sys

sys.setrecursionlimit(1_000_000)


def construct(n: int):
    if n == 1:
        return [0]

    # If n is a power of two, a standard Gray code works.
    if (n & (n - 1)) == 0:
        return [i ^ (i >> 1) for i in range(n)]

    m = 1 << (n.bit_length() - 1)  # largest power of two <= n
    r = n - m

    # A valid path for [0, r - 1]
    p = construct(r)
    bridge = p[-1]

    # First visit [m, m + r - 1] by lifting the path for [0, r - 1].
    ans = [m | x for x in p]

    # Then visit all [0, m - 1] using a Gray code starting from bridge.
    ans.extend(((i ^ (i >> 1)) ^ bridge) for i in range(m))

    return ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    out = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        idx += 1

        ans = construct(n)
        out.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()