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

        razors = {}
        for _ in range(m):
            x = data[idx]
            idx += 1
            razors[x] = razors.get(x, 0) + 1

        possible = True

        for i in range(n):
            if a[i] < b[i]:
                possible = False
                break

        if possible:
            stack = []

            for i in range(n):
                ai = a[i]
                bi = b[i]

                while stack and stack[-1] < bi:
                    stack.pop()

                if ai > bi:
                    if not stack or stack[-1] != bi:
                        if razors.get(bi, 0) == 0:
                            possible = False
                            break

                        razors[bi] -= 1
                        stack.append(bi)

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()