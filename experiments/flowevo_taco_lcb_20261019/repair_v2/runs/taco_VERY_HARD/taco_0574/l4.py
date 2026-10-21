import sys


def build_sequence(k: int):
    if k == 1:
        return [1]
    if k == 2:
        return [3, 4]

    if k % 2 == 0:
        t = k // 2
        return [t - 1, 1] + [1] * (k - 2)
    else:
        t = (k - 1) // 2
        return [t + 1, 2] + [1] * (k - 2)


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n, m = map(int, data[:2])

    rows = build_sequence(n)
    cols = build_sequence(m)

    output = []
    for r in rows:
        output.append(" ".join(str(r * c) for c in cols))

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()