import sys
import bisect


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    roots = data[2:2 + n]
    roots.sort()

    answers = []
    query_start = 2 + n

    for i in range(q):
        x = data[query_start + i]
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
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()