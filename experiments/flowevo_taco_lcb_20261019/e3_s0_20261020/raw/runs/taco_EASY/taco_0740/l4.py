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

        depth = [0] * n
        stack = [(0, n - 1, 0)]

        while stack:
            left, right, d = stack.pop()
            if left > right:
                continue

            max_pos = left
            for i in range(left + 1, right + 1):
                if a[i] > a[max_pos]:
                    max_pos = i

            depth[max_pos] = d

            stack.append((left, max_pos - 1, d + 1))
            stack.append((max_pos + 1, right, d + 1))

        answers.append(" ".join(map(str, depth)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()