import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    if max(a) - min(a) > k:
        sys.stdout.write("NO\n")
        return

    colors = [str(i + 1) for i in range(k)]
    out = ["YES"]

    for x in a:
        out.append(" ".join(colors[j % k] for j in range(x)))

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    main()