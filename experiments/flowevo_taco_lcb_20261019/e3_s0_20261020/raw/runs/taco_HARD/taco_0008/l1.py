import sys
from bisect import bisect_left, bisect_right


def solve_side(a, b):
    if not a or not b:
        return 0

    special = set(b)
    n = len(a)

    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + (1 if a[i] in special else 0)

    ans = suffix[0]

    for i, r in enumerate(b):
        k = bisect_right(a, r)
        if k == 0:
            continue

        left = r - k + 1
        first = bisect_left(b, left)

        covered_specials = i - first + 1
        cur = covered_specials + suffix[k]
        if cur > ans:
            ans = cur

    return ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        a = [next(it) for _ in range(n)]
        b = [next(it) for _ in range(m)]

        a_pos = [x for x in a if x > 0]
        b_pos = [x for x in b if x > 0]

        a_neg = [-x for x in reversed(a) if x < 0]
        b_neg = [-x for x in reversed(b) if x < 0]

        ans = solve_side(a_pos, b_pos) + solve_side(a_neg, b_neg)
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()