import sys
from bisect import bisect_left

class Fenwick:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)

    def add(self, idx, val):
        while idx <= self.n:
            self.bit[idx] += val
            idx += idx & -idx

    def sum(self, idx):
        res = 0
        while idx > 0:
            res += self.bit[idx]
            idx -= idx & -idx
        return res


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    segments = []
    right_ends = []

    p = 1
    for i in range(n):
        l = data[p]
        r = data[p + 1]
        p += 2
        segments.append((l, r, i))
        right_ends.append(r)

    right_ends.sort()
    bit = Fenwick(n)
    answer = [0] * n

    segments.sort(key=lambda x: x[0], reverse=True)

    for l, r, idx in segments:
        rank = bisect_left(right_ends, r) + 1
        answer[idx] = bit.sum(rank - 1)
        bit.add(rank, 1)

    sys.stdout.write("\n".join(map(str, answer)))


if __name__ == "__main__":
    main()