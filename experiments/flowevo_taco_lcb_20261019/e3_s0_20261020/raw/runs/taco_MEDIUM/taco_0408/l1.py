import sys

def main():
    input_data = sys.stdin.buffer
    first = input_data.readline().split()
    if not first:
        return

    n, m, k = map(int, first)

    pairs = []

    if k == 0:
        # Sort ascending using adjacent compare-exchanges:
        # swap (i, i+1) if value[i] > value[i+1]
        for end in range(m, 1, -1):
            for i in range(1, end):
                pairs.append((i, i + 1))
    else:
        # Sort descending using the reversed comparator:
        # swap (i+1, i) if value[i+1] > value[i]
        for end in range(m, 1, -1):
            for i in range(1, end):
                pairs.append((i + 1, i))

    output = [str(len(pairs))]
    output.extend(f"{i} {j}" for i, j in pairs)
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()