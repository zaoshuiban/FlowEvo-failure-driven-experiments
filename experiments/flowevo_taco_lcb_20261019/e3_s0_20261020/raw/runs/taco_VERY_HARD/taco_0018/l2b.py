import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, r = data[0], data[1]
    size = 1 << n

    values = data[2:2 + size]
    total = sum(values)

    idx = 2 + size
    ans = []

    ans.append(f"{total / size:.15f}")

    for _ in range(r):
        z = data[idx]
        g = data[idx + 1]
        idx += 2

        total += g - values[z]
        values[z] = g

        ans.append(f"{total / size:.15f}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()