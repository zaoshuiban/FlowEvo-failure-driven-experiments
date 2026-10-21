import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    k = int(data[2])

    pairs = []

    # Insertion sort network:
    # This fixed sequence of adjacent comparisons sorts any array.
    for r in range(1, m):
        for j in range(r, 0, -1):
            left = j - 1
            right = j

            if k == 0:
                # Ascending comparator: ensure a[left] <= a[right]
                pairs.append((left + 1, right + 1))
            else:
                # Descending comparator: ensure a[left] >= a[right]
                pairs.append((right + 1, left + 1))

    output = [str(len(pairs))]
    output.extend(f"{a} {b}" for a, b in pairs)
    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()