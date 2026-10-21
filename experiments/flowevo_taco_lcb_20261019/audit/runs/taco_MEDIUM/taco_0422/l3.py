import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        results = []

        if n % 2 == 1:
            for i in range(1, n + 1):
                for j in range(i + 1, n + 1):
                    results.append("1" if (i + j) % 2 == 1 else "-1")
        else:
            half = n // 2
            for i in range(1, n + 1):
                for j in range(i + 1, n + 1):
                    distance = j - i
                    if distance == half:
                        results.append("0")
                    elif distance < half:
                        results.append("1")
                    else:
                        results.append("-1")

        output.append(" ".join(results))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()