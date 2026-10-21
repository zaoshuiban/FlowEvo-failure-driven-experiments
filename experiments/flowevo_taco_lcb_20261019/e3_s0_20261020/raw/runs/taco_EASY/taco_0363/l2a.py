import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = [0] * (n + 1)

    for i, p in enumerate(data[1:], start=2):
        parent[i] = p

    path = []
    current = n

    while current != 0:
        path.append(current)
        current = parent[current]

    path.reverse()
    sys.stdout.write(" ".join(map(str, path)))

if __name__ == "__main__":
    main()