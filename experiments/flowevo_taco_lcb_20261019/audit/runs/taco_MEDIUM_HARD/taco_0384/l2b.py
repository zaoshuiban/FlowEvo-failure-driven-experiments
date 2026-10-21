import sys
from collections import Counter


def solve():
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

        razors = Counter(data[idx:idx + m])
        idx += m

        possible = True
        need = {}
        stack = []

        for ai, bi in zip(a, b):
            if ai < bi:
                possible = False

            while stack and stack[-1] < bi:
                stack.pop()

            if ai > bi:
                if not stack or stack[-1] != bi:
                    need[bi] = need.get(bi, 0) + 1
                    stack.append(bi)

        if possible:
            for height, required in need.items():
                if razors.get(height, 0) < required:
                    possible = False
                    break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()