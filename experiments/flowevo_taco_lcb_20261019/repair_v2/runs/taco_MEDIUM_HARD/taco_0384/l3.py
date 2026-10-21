import sys
from collections import Counter


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    ptr = 0

    t = data[ptr]
    ptr += 1

    answers = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        a = data[ptr:ptr + n]
        ptr += n

        b = data[ptr:ptr + n]
        ptr += n

        m = data[ptr]
        ptr += 1

        razors = Counter(data[ptr:ptr + m])
        ptr += m

        possible = True

        for i in range(n):
            if a[i] < b[i]:
                possible = False
                break

        if possible:
            stack = []

            for i in range(n):
                bi = b[i]

                while stack and stack[-1] < bi:
                    stack.pop()

                if a[i] > bi:
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