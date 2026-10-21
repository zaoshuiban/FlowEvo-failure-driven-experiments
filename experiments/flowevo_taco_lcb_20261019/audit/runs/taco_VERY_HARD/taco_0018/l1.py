import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    r = int(next(it))

    m = 1 << n
    c = [0] * m
    total = 0

    for i in range(m):
        c[i] = int(next(it))
        total += c[i]

    out = []
    out.append(f"{total / m:.10f}")

    for _ in range(r):
        z = int(next(it))
        g = int(next(it))

        total += g - c[z]
        c[z] = g

        out.append(f"{total / m:.10f}")

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    main()