import sys
import heapq


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        m = next_int()

        adj = [[] for _ in range(n)]

        for _ in range(m):
            u = next_int() - 1
            v = next_int() - 1
            adj[u].append(v)
            adj[v].append(u)

        labels = [0] * n
        used = bytearray(n)

        heap = [(0, i) for i in range(n)]
        heapq.heapify(heap)

        max_clique = 1

        for _ in range(n):
            while True:
                neg_label, v = heapq.heappop(heap)
                if not used[v] and -neg_label == labels[v]:
                    break

            used[v] = 1
            current_label = labels[v]
            max_clique = max(max_clique, current_label + 1)

            for nei in adj[v]:
                if not used[nei]:
                    labels[nei] += 1
                    heapq.heappush(heap, (-labels[nei], nei))

        answers.append(str(max_clique))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()