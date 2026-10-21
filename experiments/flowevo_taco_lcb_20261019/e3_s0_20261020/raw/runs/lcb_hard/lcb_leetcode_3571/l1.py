from typing import List

class FenwickMax:
    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (n + 2)

    def update(self, i: int, value: int) -> None:
        while i <= self.n:
            if value > self.tree[i]:
                self.tree[i] = value
            i += i & -i

    def query(self, i: int) -> int:
        result = 0
        while i > 0:
            if self.tree[i] > result:
                result = self.tree[i]
            i -= i & -i
        return result


class Solution:
    def maxPathLength(self, coordinates: List[List[int]], k: int) -> int:
        n = len(coordinates)

        ys = sorted({y for _, y in coordinates})
        rank = {y: i + 1 for i, y in enumerate(ys)}
        m = len(ys)

        points = [(coordinates[i][0], coordinates[i][1], i) for i in range(n)]
        points.sort(key=lambda p: (p[0], p[1]))

        dp_end = [0] * n
        bit = FenwickMax(m)

        i = 0
        while i < n:
            j = i + 1
            x = points[i][0]

            while j < n and points[j][0] == x:
                j += 1

            for t in range(i, j):
                _, y, idx = points[t]
                r = rank[y]
                dp_end[idx] = bit.query(r - 1) + 1

            for t in range(i, j):
                _, y, idx = points[t]
                r = rank[y]
                bit.update(r, dp_end[idx])

            i = j

        dp_start = [0] * n
        bit = FenwickMax(m)

        i = n - 1
        while i >= 0:
            x = points[i][0]
            j = i - 1

            while j >= 0 and points[j][0] == x:
                j -= 1

            for t in range(j + 1, i + 1):
                _, y, idx = points[t]
                r = rank[y]
                reversed_r = m - r + 1
                dp_start[idx] = bit.query(reversed_r - 1) + 1

            for t in range(j + 1, i + 1):
                _, y, idx = points[t]
                r = rank[y]
                reversed_r = m - r + 1
                bit.update(reversed_r, dp_start[idx])

            i = j

        return dp_end[k] + dp_start[k] - 1