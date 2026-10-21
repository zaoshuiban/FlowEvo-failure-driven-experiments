import sys


def build_sequence(k: int):
    if k == 1:
        return [1]
    if k == 2:
        return [3, 4]

    d = k - 2

    if d % 2 == 0:
        b = 1
        a = d // 2
    else:
        b = 2
        a = (d + 3) // 2

    return [a, b] + [1] * d


def main():
    n, m = map(int, sys.stdin.readline().split())

    rows = build_sequence(n)
    cols = build_sequence(m)

    answer = []
    for x in rows:
        answer.append(" ".join(str(x * y) for y in cols))

    sys.stdout.write("\n".join(answer))


if __name__ == "__main__":
    main()