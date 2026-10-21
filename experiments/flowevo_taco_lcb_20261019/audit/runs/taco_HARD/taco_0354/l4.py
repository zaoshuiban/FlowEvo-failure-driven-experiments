import sys
import heapq


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    p = 0
    t = data[p]
    p += 1

    answers = []

    for _ in range(t):
        n = data[p]
        q = data[p + 1]
        p += 2

        a = data[p:p + n]
        p += n

        m = n - 1  # Number of adjacent differences
        diff = [0] * m
        heap = []

        for i in range(m):
            diff[i] = a[i] - a[i + 1]
            heap.append((-diff[i], i))

        heapq.heapify(heap)

        for _ in range(q):
            idx = data[p] - 1
            x = data[p + 1]
            p += 2

            if a[idx] != x:
                a[idx] = x

                pos = idx - 1
                if 0 <= pos < m:
                    val = a[pos] - a[pos + 1]
                    diff[pos] = val
                    heapq.heappush(heap, (-val, pos))

                pos = idx
                if 0 <= pos < m:
                    val = a[pos] - a[pos + 1]
                    diff[pos] = val
                    heapq.heappush(heap, (-val, pos))

            while heap:
                neg_val, pos = heap[0]
                if diff[pos] == -neg_val:
                    break
                heapq.heappop(heap)

            if heap:
                best = -heap[0][0]
                if best < 0:
                    best = 0
            else:
                best = 0

            answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()