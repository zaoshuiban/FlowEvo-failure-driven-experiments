import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = [0] * (n + 1)

    for i in range(2, n + 1):
        parent[i] = data[i - 1]

    path = []
    current = n

    while current != 0:
        path.append(current)
        current = parent[current]

    path.reverse()

    sys.stdout.write(" ".join(map(str, path)) + "\n")

if __name__ == "__main__":
    main()