import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        b = data[idx:idx + n]
        idx += n

        m = data[idx]
        idx += 1

        razors = data[idx:idx + m]
        idx += m

        possible = True

        for i in range(n):
            if a[i] < b[i]:
                possible = False
                break

        if not possible:
            answers.append("NO")
            continue

        needed = {}
        stack = []

        for i in range(n):
            y = b[i]

            while stack and stack[-1] < y:
                stack.pop()

            if a[i] > y:
                if not stack or stack[-1] != y:
                    needed[y] = needed.get(y, 0) + 1
                    stack.append(y)

        available = {}
        for x in razors:
            available[x] = available.get(x, 0) + 1

        for value, count in needed.items():
            if available.get(value, 0) < count:
                possible = False
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()