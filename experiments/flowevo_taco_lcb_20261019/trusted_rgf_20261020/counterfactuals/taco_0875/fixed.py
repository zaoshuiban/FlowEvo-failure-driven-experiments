import sys
sys.setrecursionlimit(10000)

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = [-1] * (n + 1)

    for i in range(1, n + 1):
        parent[i] = data[i]

    depth = [0] * (n + 1)

    def get_depth(employee):
        if depth[employee] != 0:
            return depth[employee]

        if parent[employee] == -1:
            depth[employee] = 1
        else:
            depth[employee] = get_depth(parent[employee]) + 1

        return depth[employee]

    answer = 0
    for i in range(1, n + 1):
        answer = max(answer, get_depth(i))

    print(answer)

if __name__ == "__main__":
    main()