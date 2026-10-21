import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    r = next(it)

    size = 1 << n
    values = [next(it) for _ in range(size)]
    total = sum(values)

    ans = []
    ans.append(f"{total / size:.10f}")

    for _ in range(r):
        z = next(it)
        g = next(it)
        total += g - values[z]
        values[z] = g
        ans.append(f"{total / size:.10f}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()