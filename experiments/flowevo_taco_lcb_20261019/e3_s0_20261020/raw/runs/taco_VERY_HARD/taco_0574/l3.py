import sys


def build_sequence(k: int):
    if k == 1:
        return [1]
    if k == 2:
        return [3, 4]
    if k == 3:
        return [1, 2, 2]

    if k % 2 == 0:
        y = 1
    else:
        y = 2

    x = (y * y + k - 3) // 2
    return [x, y] + [1] * (k - 2)


def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n, m = map(int, data[:2])

    rows = build_sequence(n)
    cols = build_sequence(m)

    result = []
    for r in rows:
        result.append(" ".join(str(r * c) for c in cols))

    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    main()