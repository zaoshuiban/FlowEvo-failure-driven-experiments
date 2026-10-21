import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        left = [-1] * n
        right = [-1] * n
        parent = [-1] * n
        stack = []

        for i in range(n):
            last = -1

            while stack and a[stack[-1]] < a[i]:
                last = stack.pop()

            if stack:
                parent[i] = stack[-1]
                right[stack[-1]] = i

            if last != -1:
                parent[last] = i
                left[i] = last

            stack.append(i)

        root = 0
        for i in range(n):
            if parent[i] == -1:
                root = i
                break

        depth = [0] * n
        traversal = [(root, 0)]

        while traversal:
            node, d = traversal.pop()
            depth[node] = d

            if left[node] != -1:
                traversal.append((left[node], d + 1))
            if right[node] != -1:
                traversal.append((right[node], d + 1))

        answers.append(" ".join(map(str, depth)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()