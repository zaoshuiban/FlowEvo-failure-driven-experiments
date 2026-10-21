import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = []

    for x in data[1:n + 1]:
        if x == -1:
            parent.append(-1)
        else:
            parent.append(x - 1)

    depth = [0] * n

    for i in range(n):
        if depth[i] != 0:
            continue

        stack = []
        cur = i

        while cur != -1 and depth[cur] == 0:
            stack.append(cur)
            cur = parent[cur]

        current_depth = 0 if cur == -1 else depth[cur]

        while stack:
            node = stack.pop()
            current_depth += 1
            depth[node] = current_depth

    print(max(depth))

if __name__ == "__main__":
    main()