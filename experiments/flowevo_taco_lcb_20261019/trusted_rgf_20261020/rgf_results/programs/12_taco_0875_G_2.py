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
    answer = 0

    for i in range(1, n + 1):
        if depth[i] == 0:
            stack = []
            current = i

            while current != -1 and depth[current] == 0:
                stack.append(current)
                current = parent[current]

            current_depth = depth[current] if current != -1 else 0

            while stack:
                employee = stack.pop()
                current_depth += 1
                depth[employee] = current_depth

        answer = max(answer, depth[i])

    print(answer)


if __name__ == "__main__":
    main()
