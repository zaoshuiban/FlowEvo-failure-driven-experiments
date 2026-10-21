import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:1 + n]

    pos = [0] * (n + 1)
    for idx in range(1, n + 1):
        pos[a[idx]] = idx

    operations = []

    for i in range(1, n + 1):
        if a[i] != i:
            p = pos[i]
            v = a[i]

            a[i], a[p] = a[p], a[i]

            pos[v] = p
            pos[i] = i

            operations.append((i, p))

    output = [str(len(operations))]
    output.extend(f"{i} {j}" for i, j in operations)

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()