import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    parents = data[1:1 + n]

    children = [[] for _ in range(n)]
    roots = []

    for i, p in enumerate(parents):
        if p == -1:
            roots.append(i)
        else:
            children[p - 1].append(i)

    max_depth = 0
    stack = [(root, 1) for root in roots]

    while stack:
        employee, depth = stack.pop()
        max_depth = max(max_depth, depth)

        for child in children[employee]:
            stack.append((child, depth + 1))

    print(max_depth)

if __name__ == "__main__":
    main()