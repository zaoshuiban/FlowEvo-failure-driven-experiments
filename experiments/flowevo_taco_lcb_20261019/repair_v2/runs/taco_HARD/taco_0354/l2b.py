import sys
import heapq


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        q = next(it)

        a = [next(it) for _ in range(n)]

        # b[i] = a[i] - a[i + 1], for i = 0 .. n-2
        b = [0] * max(0, n - 1)
        heap = []

        for i in range(n - 1):
            b[i] = a[i] - a[i + 1]
            heapq.heappush(heap, (-b[i], i))

        for _ in range(q):
            idx = next(it) - 1
            x = next(it)

            if a[idx] != x:
                a[idx] = x

                if idx - 1 >= 0:
                    pos = idx - 1
                    b[pos] = a[pos] - a[pos + 1]
                    heapq.heappush(heap, (-b[pos], pos))

                if idx <= n - 2:
                    pos = idx
                    b[pos] = a[pos] - a[pos + 1]
                    heapq.heappush(heap, (-b[pos], pos))

            while heap and -heap[0][0] != b[heap[0][1]]:
                heapq.heappop(heap)

            max_drop = -heap[0][0] if heap else 0
            answers.append(str(max(0, max_drop)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()