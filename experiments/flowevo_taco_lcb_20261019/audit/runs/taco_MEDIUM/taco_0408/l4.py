import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    k = int(data[2])

    operations = []

    if k == 0:
        # Ascending bubble-sort comparator network
        for end in range(m, 1, -1):
            for i in range(1, end):
                operations.append((i, i + 1))
    else:
        # Descending bubble-sort comparator network
        for end in range(m, 1, -1):
            for i in range(1, end):
                operations.append((i + 1, i))

    output = [str(len(operations))]
    output.extend(f"{a} {b}" for a, b in operations)
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    solve()