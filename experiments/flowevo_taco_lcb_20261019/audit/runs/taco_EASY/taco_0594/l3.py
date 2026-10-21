import sys
import heapq
from collections import defaultdict


def squarefree_part(x: int) -> int:
    res = 1
    p = 2

    while p * p <= x:
        parity = 0
        while x % p == 0:
            x //= p
            parity ^= 1
        if parity:
            res *= p
        p += 1

    if x > 1:
        res *= x

    return res


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ns = data[1:1 + t]

    max_n = max(ns) if ns else 0

    sf = [0] * (max_n + 1)
    for i in range(1, max_n + 1):
        sf[i] = squarefree_part(i)

    answers = []

    for n in ns:
        groups = defaultdict(list)

        for value in range(1, n + 1):
            groups[sf[value]].append(value)

        heap = [(-len(values), key) for key, values in groups.items()]
        heapq.heapify(heap)

        ans = []
        prev_key = None
        prev_remaining = 0

        for _ in range(n):
            neg_count, key = heapq.heappop(heap)

            ans.append(groups[key].pop())
            remaining = -neg_count - 1

            if prev_key is not None and prev_remaining > 0:
                heapq.heappush(heap, (-prev_remaining, prev_key))

            prev_key = key
            prev_remaining = remaining

        answers.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()