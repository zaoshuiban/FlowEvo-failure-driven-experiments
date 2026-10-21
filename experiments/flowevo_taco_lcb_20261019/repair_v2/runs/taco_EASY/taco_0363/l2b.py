import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    parent = [0] * (n + 1)

    idx = 1
    for i in range(2, n + 1):
        parent[i] = data[idx]
        idx += 1

    path = []
    current = n

    while current != 0:
        path.append(current)
        current = parent[current]

    path.reverse()

    sys.stdout.write(" ".join(map(str, path)))

if __name__ == "__main__":
    main()