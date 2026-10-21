import sys
from bisect import bisect_left

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    q = next(it)

    roots = [next(it) for _ in range(n)]
    roots.sort()

    answers = []

    for _ in range(q):
        x = next(it)
        pos = bisect_left(roots, x)

        if pos < n and roots[pos] == x:
            answers.append("0")
        else:
            # Number of negative factors is n - pos
            if (n - pos) % 2 == 1:
                answers.append("NEGATIVE")
            else:
                answers.append("POSITIVE")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()