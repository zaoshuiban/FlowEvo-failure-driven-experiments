import sys

def main():
    input = sys.stdin.buffer.readline
    n = int(input())
    deps = [[] for _ in range(n)]
    for i in range(n):
        parts = list(map(int, input().split()))
        c = parts[0]
        if c > 0:
            deps[i] = [x - 1 for x in parts[1:c + 1]]

    visited = [False] * n
    postorder = []
    stack = [(0, 0)]  # (book, state): 0 = enter, 1 = exit

    while stack:
        v, state = stack.pop()
        if state == 0:
            if visited[v]:
                continue
            visited[v] = True
            stack.append((v, 1))
            for u in deps[v]:
                if not visited[u]:
                    stack.append((u, 0))
        else:
            postorder.append(v)

    answer = [str(v + 1) for v in postorder if v != 0]
    print(" ".join(answer))

if __name__ == "__main__":
    main()