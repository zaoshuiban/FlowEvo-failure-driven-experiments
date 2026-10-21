import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    k = int(data[2])

    operations = []

    if k == 0:
        # Bubble-sort network for ascending order
        for last in range(m, 1, -1):
            for i in range(1, last):
                operations.append((i, i + 1))
    else:
        # Bubble-sort network for descending order
        for last in range(m, 1, -1):
            for i in range(1, last):
                operations.append((i + 1, i))

    output = [str(len(operations))]
    output.extend(f"{i} {j}" for i, j in operations)

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    main()