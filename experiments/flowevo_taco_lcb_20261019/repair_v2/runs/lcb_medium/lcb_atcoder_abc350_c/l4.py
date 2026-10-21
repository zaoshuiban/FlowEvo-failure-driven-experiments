import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    pos = [0] * (n + 1)
    for i, value in enumerate(a):
        pos[value] = i

    operations = []

    for i in range(n - 1):
        target = i + 1
        if a[i] != target:
            j = pos[target]
            old = a[i]

            a[i], a[j] = a[j], a[i]

            pos[target] = i
            pos[old] = j

            operations.append((i + 1, j + 1))

    output = [str(len(operations))]
    output.extend(f"{i} {j}" for i, j in operations)

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    solve()