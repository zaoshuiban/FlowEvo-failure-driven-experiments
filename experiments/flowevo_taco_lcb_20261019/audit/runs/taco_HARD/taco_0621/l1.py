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

        arr = [1]
        total = 1
        cur = 1

        while total < n:
            cur <<= 1
            x = min(cur, n - total)
            arr.append(x)
            total += x

        arr.sort()

        days = len(arr) - 1
        splits = [arr[i] - arr[i - 1] for i in range(1, len(arr))]

        output.append(str(days))
        output.append(" ".join(map(str, splits)))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()