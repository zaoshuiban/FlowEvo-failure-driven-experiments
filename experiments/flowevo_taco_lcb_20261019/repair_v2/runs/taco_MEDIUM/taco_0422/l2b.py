import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        results = []
        for i in range(n):
            for j in range(i + 1, n):
                distance = j - i

                if 2 * distance < n:
                    results.append("1")
                elif 2 * distance == n:
                    results.append("0")
                else:
                    results.append("-1")

        output.append(" ".join(results))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()