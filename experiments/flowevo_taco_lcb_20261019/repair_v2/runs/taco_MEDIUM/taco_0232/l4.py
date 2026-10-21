import sys
import bisect


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    # Single test case format: N Q, then N roots, then Q queries
    if len(data) >= 2:
        n0, q0 = data[0], data[1]
        if n0 >= 1 and q0 >= 1 and len(data) == 2 + n0 + q0:
            n, q = n0, q0
            roots = data[2:2 + n]
            roots.sort()

            answers = []
            ptr = 2 + n

            for _ in range(q):
                x = data[ptr]
                ptr += 1

                idx = bisect.bisect_left(roots, x)
                if idx < n and roots[idx] == x:
                    answers.append("0")
                else:
                    greater_roots = n - idx
                    if greater_roots % 2 == 1:
                        answers.append("NEGATIVE")
                    else:
                        answers.append("POSITIVE")

            sys.stdout.write("\n".join(answers))
            return

    # Multiple test case format: T, then T test cases
    t = data[0]
    ptr = 1
    answers = []

    for _ in range(t):
        n = data[ptr]
        q = data[ptr + 1]
        ptr += 2

        roots = data[ptr:ptr + n]
        ptr += n
        roots.sort()

        for _ in range(q):
            x = data[ptr]
            ptr += 1

            idx = bisect.bisect_left(roots, x)
            if idx < n and roots[idx] == x:
                answers.append("0")
            else:
                greater_roots = n - idx
                if greater_roots % 2 == 1:
                    answers.append("NEGATIVE")
                else:
                    answers.append("POSITIVE")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()