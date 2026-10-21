import sys
from collections import deque

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:1 + n]

    indeg = [0] * (n + 1)
    for i in range(1, n + 1):
        indeg[a[i]] += 1

    q = deque(i for i in range(1, n + 1) if indeg[i] == 0)

    while q:
        u = q.popleft()
        v = a[u]
        indeg[v] -= 1
        if indeg[v] == 0:
            q.append(v)

    visited = [False] * (n + 1)
    cycles = []

    for i in range(1, n + 1):
        if indeg[i] > 0 and not visited[i]:
            cur = i
            is_self_loop = (a[i] == i)

            while not visited[cur]:
                visited[cur] = True
                cur = a[cur]

            cycles.append((i, is_self_loop))

    self_cycles = [rep for rep, is_self_loop in cycles if is_self_loop]
    ans = 0

    if self_cycles:
        final_root = self_cycles[0]

        for r in self_cycles[1:]:
            a[r] = final_root
            ans += 1

        for rep, is_self_loop in cycles:
            if not is_self_loop:
                a[rep] = final_root
                ans += 1

    else:
        final_root = cycles[0][0]
        a[final_root] = final_root
        ans = 1

        for rep, _ in cycles[1:]:
            a[rep] = final_root
            ans += 1

    sys.stdout.write(str(ans) + "\n")
    sys.stdout.write(" ".join(map(str, a[1:])) + "\n")


if __name__ == "__main__":
    main()