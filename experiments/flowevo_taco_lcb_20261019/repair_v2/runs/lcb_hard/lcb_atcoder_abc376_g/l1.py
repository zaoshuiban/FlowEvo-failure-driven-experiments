import sys
import heapq

MOD = 998244353


class Entry:
    __slots__ = ("w", "t", "id", "ver")

    def __init__(self, w, t, idx, ver):
        self.w = w
        self.t = t
        self.id = idx
        self.ver = ver

    def __lt__(self, other):
        # Max-heap by density w / t using exact cross multiplication.
        lhs = self.w * other.t
        rhs = other.w * self.t
        if lhs != rhs:
            return lhs > rhs
        if self.id != other.id:
            return self.id < other.id
        return self.ver < other.ver


def dsu_find(dsu, x):
    while dsu[x] != x:
        dsu[x] = dsu[dsu[x]]
        x = dsu[x]
    return x


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    T = data[idx]
    idx += 1

    answers = []
    heappush = heapq.heappush
    heappop = heapq.heappop
    heapify = heapq.heapify

    for _ in range(T):
        N = data[idx]
        idx += 1

        if N == 1:
            # Only vertex 1 can contain the treasure, and it is always searched once.
            idx += 2  # skip p1 and a1
            answers.append("1")
            continue

        parent = [0] * (N + 1)
        for i in range(1, N + 1):
            parent[i] = data[idx]
            idx += 1

        dsu = list(range(N + 1))
        weight = [0] * (N + 1)
        time = [0] * (N + 1)
        cost = [0] * (N + 1)
        active = bytearray(N + 1)
        version = [0] * (N + 1)

        heap = []
        total_weight = 0

        for i in range(1, N + 1):
            ai = data[idx]
            idx += 1

            weight[i] = ai
            time[i] = 1
            cost[i] = ai % MOD
            active[i] = 1
            total_weight += ai

            heap.append(Entry(ai, 1, i, 0))

        heapify(heap)

        for _ in range(N):
            while True:
                e = heappop(heap)
                x = e.id
                if active[x] and e.ver == version[x]:
                    break

            y = dsu_find(dsu, parent[x])

            cost[y] = (cost[y] + cost[x] + time[y] * weight[x]) % MOD
            weight[y] += weight[x]
            time[y] += time[x]

            active[x] = 0
            dsu[x] = y

            if y != 0:
                version[y] += 1
                heappush(heap, Entry(weight[y], time[y], y, version[y]))

        ans = cost[0] * pow(total_weight, MOD - 2, MOD) % MOD
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()