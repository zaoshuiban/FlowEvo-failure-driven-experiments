import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parents = data[1:n + 1]

    children = [[] for _ in range(n)]
    roots = []

    for i, p in enumerate(parents):
        if p == -1:
            roots.append(i)
        else:
            children[p - 1].append(i)

    max_groups = 0
    stack = [(root, 1) for root in roots]

    while stack:
        employee, depth = stack.pop()
        if depth > max_groups:
            max_groups = depth

        for child in children[employee]:
            stack.append((child, depth + 1))

    print(max_groups)

if __name__ == "__main__":
    main()