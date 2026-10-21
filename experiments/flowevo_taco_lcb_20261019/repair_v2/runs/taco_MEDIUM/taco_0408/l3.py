import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    m = int(data[1])
    k = int(data[2])

    pairs = []

    for i in range(1, m + 1):
        for j in range(i + 1, m + 1):
            if k == 0:
                pairs.append((i, j))
            else:
                pairs.append((j, i))

    output = [str(len(pairs))]
    output.extend(f"{a} {b}" for a, b in pairs)
    sys.stdout.write("\n".join(output) + "\n")

if __name__ == "__main__":
    solve()