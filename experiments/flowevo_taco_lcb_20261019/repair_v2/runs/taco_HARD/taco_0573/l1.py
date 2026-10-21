import sys
from bisect import bisect_right


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    a = [next(it) for _ in range(n)]

    m = next(it)
    queries = []
    for idx in range(m):
        t = next(it)
        d = next(it)
        queries.append((d, t, idx))

    gaps = []
    for j in range(1, n):  # gap between a[j - 1] and a[j], 1-based position j
        gaps.append((a[j] - a[j - 1], j))

    gaps.sort(reverse=True)
    queries.sort(reverse=True)

    bit = [0] * (n + 2)

    def update(i, value):
        while i <= n:
            if value > bit[i]:
                bit[i] = value
            i += i & -i

    def query(i):
        result = 0
        while i > 0:
            if bit[i] > result:
                result = bit[i]
            i -= i & -i
        return result

    answers = [0] * m
    gap_idx = 0

    for d, t, idx in queries:
        while gap_idx < len(gaps) and gaps[gap_idx][0] > d:
            pos = gaps[gap_idx][1]
            update(pos, pos)
            gap_idx += 1

        k = bisect_right(a, t)  # number of elements <= t, also 1-based index of last such element
        last_bad_gap = query(k - 1)

        answers[idx] = last_bad_gap + 1

    sys.stdout.write("\n".join(map(str, answers)))


if __name__ == "__main__":
    main()