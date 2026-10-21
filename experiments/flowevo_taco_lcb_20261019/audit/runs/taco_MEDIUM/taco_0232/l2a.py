import sys
import bisect

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    roots = sorted(data[2:2 + n])
    queries = data[2 + n:2 + n + q]

    answers = []
    for x in queries:
        idx = bisect.bisect_left(roots, x)

        if idx < n and roots[idx] == x:
            answers.append("0")
        else:
            # Number of negative factors is the number of roots greater than x.
            if (n - idx) % 2 == 1:
                answers.append("NEGATIVE")
            else:
                answers.append("POSITIVE")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()