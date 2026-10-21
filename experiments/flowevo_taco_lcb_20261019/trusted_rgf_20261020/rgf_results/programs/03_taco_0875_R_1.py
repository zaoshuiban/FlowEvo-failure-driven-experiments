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

    for i in range(1, n + 1):
        if depth[i] != 0:
            continue

        path = []
        cur = i

        while cur != -1 and depth[cur] == 0:
            path.append(cur)
            cur = parent[cur]

        for employee in reversed(path):
            p = parent[employee]
            depth[employee] = 1 if p == -1 else depth[p] + 1

    print(max(depth[1:]))

if __name__ == "__main__":
    main()
