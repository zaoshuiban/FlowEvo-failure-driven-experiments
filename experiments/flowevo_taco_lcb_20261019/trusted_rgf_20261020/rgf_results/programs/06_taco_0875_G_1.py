import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = [-1] * (n + 1)

    for i in range(1, n + 1):
        parent[i] = data[i]

    depth = [0] * (n + 1)

    for start in range(1, n + 1):
        if depth[start] != 0:
            continue

        path = []
        current = start

        while current != -1 and depth[current] == 0:
            path.append(current)
            current = parent[current]

        current_depth = 0 if current == -1 else depth[current]

        for employee in reversed(path):
            current_depth += 1
            depth[employee] = current_depth

    print(max(depth))

if __name__ == "__main__":
    main()
