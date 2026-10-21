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

        # diff[i] = a[i] - a[i + 1]
        diff = [0] * (n - 1)
        heap = []

        for i in range(n - 1):
            diff[i] = a[i] - a[i + 1]
            heap.append((-diff[i], i))

        heapq.heapify(heap)

        for _ in range(q):
            pos = next(it) - 1
            value = next(it)

            if a[pos] != value:
                a[pos] = value

                idx = pos - 1
                if 0 <= idx < n - 1:
                    new_diff = a[idx] - a[idx + 1]
                    diff[idx] = new_diff
                    heapq.heappush(heap, (-new_diff, idx))

                idx = pos
                if 0 <= idx < n - 1:
                    new_diff = a[idx] - a[idx + 1]
                    diff[idx] = new_diff
                    heapq.heappush(heap, (-new_diff, idx))

            while heap:
                neg_value, idx = heap[0]
                if -neg_value == diff[idx]:
                    break
                heapq.heappop(heap)

            max_drop = -heap[0][0] if heap else 0
            if max_drop < 0:
                max_drop = 0

            answers.append(str(max_drop))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()