import sys


def full_path(size, start):
    # Hamiltonian path of the full hypercube [0, size) starting at start.
    # size must be a power of two.
    return [start ^ (i ^ (i >> 1)) for i in range(size)]


def construct(n):
    if (n & (n - 1)) == 0:
        return full_path(n, 0)

    p = 1 << (n.bit_length() - 1)  # largest power of two < n
    r = n - p

    pref = construct(r)
    x = pref[-1]

    res = [p + v for v in pref]
    res.extend(full_path(p, x))
    return res


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        ans = construct(n)
        answers.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()