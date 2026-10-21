import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        base = pos
        stack = []
        last = {}
        total = 0

        for i in range(n):
            v = data[base + i]

            while stack and data[base + stack[-1]] >= v:
                stack.pop()

            left_smaller = stack[-1] if stack else -1
            previous_same = last.get(v, -1)

            if previous_same <= left_smaller:
                total += 1

            last[v] = i
            stack.append(i)

        pos += n
        answers.append(str(total - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()