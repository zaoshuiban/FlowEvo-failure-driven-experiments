import sys
import heapq

def solve():
    input = sys.stdin.readline
    t = int(input())
    out = []
    for _ in range(t):
        n = int(input())
        by_m = [[] for _ in range(n)]
        for _ in range(n):
            m, p = map(int, input().split())
            by_m[m].append(p)

        heap = []
        have = 0
        cost = 0

        for i in range(n - 1, -1, -1):
            for p in by_m[i]:
                heapq.heappush(heap, p)

            while have < i:
                cost += heapq.heappop(heap)
                have += 1

        out.append(str(cost))

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    solve()