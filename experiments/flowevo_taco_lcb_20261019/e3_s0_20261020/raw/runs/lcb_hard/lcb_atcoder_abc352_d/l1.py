import sys
from collections import deque

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, K = data[0], data[1]
    P = data[2:2 + N]

    pos = [0] * (N + 1)
    for i, value in enumerate(P, start=1):
        pos[value] = i

    min_q = deque()
    max_q = deque()
    ans = N

    for v in range(1, N + 1):
        x = pos[v]

        while min_q and pos[min_q[-1]] >= x:
            min_q.pop()
        min_q.append(v)

        while max_q and pos[max_q[-1]] <= x:
            max_q.pop()
        max_q.append(v)

        if v >= K:
            left = v - K + 1

            while min_q[0] < left:
                min_q.popleft()
            while max_q[0] < left:
                max_q.popleft()

            span = pos[max_q[0]] - pos[min_q[0]]
            if span < ans:
                ans = span

    print(ans)

if __name__ == "__main__":
    solve()