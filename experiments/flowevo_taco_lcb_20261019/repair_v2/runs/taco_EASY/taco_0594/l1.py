import sys
import heapq
from collections import defaultdict


def squarefree_part(n: int) -> int:
    res = 1
    p = 2

    while p * p <= n:
        parity = 0
        while n % p == 0:
            n //= p
            parity ^= 1
        if parity:
            res *= p
        p += 1

    if n > 1:
        res *= n

    return res


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ns = data[1:1 + t]

    max_n = max(ns)
    sf = [0] * (max_n + 1)

    for x in range(1, max_n + 1):
        sf[x] = squarefree_part(x)

    output = []

    for n in ns:
        groups = defaultdict(list)

        for x in range(1, n + 1):
            groups[sf[x]].append(x)

        heap = []
        for kernel, values in groups.items():
            heap.append((-len(values), kernel))

        heapq.heapify(heap)

        answer = []

        prev_count = 0
        prev_kernel = None

        for _ in range(n):
            count, kernel = heapq.heappop(heap)
            answer.append(groups[kernel].pop())

            if prev_count < 0:
                heapq.heappush(heap, (prev_count, prev_kernel))

            prev_count = count + 1
            prev_kernel = kernel

        output.append(" ".join(map(str, answer)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()