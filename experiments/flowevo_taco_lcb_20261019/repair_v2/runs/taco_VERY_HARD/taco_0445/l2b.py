import sys
from collections import deque


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    EQ = ord('=')
    LT = ord('<')

    for _ in range(t):
        n = int(next(it))
        A = [int(next(it)) for _ in range(n)]
        S = next(it)

        comp = [0] * n
        required = []
        cid = -1
        possible = True

        for i in range(n):
            if i == 0 or S[i - 1] != EQ:
                cid += 1
                required.append(-1)

            comp[i] = cid
            val = A[i]

            if val != -1:
                if required[cid] == -1:
                    required[cid] = val
                elif required[cid] != val:
                    possible = False

        if not possible:
            answers.append("NO")
            continue

        m = cid + 1
        indegree = [0] * m
        graph = [[] for _ in range(m)]

        for i in range(n - 1):
            ch = S[i]
            if ch == EQ:
                continue

            c1 = comp[i]
            c2 = comp[i + 1]

            if ch == LT:
                u, v = c1, c2
            else:
                u, v = c2, c1

            graph[u].append(v)
            indegree[v] += 1

        values = [0] * m
        for c in range(m):
            if required[c] != -1:
                values[c] = required[c]

        q = deque()
        for c in range(m):
            if indegree[c] == 0:
                q.append(c)

        processed = 0

        while q:
            u = q.popleft()
            processed += 1
            next_value = values[u] + 1

            for v in graph[u]:
                if values[v] < next_value:
                    values[v] = next_value

                indegree[v] -= 1
                if indegree[v] == 0:
                    q.append(v)

        if processed != m:
            possible = False
        else:
            for c in range(m):
                if required[c] != -1 and values[c] != required[c]:
                    possible = False
                    break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()