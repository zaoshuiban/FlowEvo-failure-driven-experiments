import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    length = data[idx]
    idx += 1
    prev = data[idx:idx + length]
    idx += length

    graph = [[] for _ in range(m + 1)]
    must_be_large = [False] * (m + 1)
    must_be_small = [False] * (m + 1)

    impossible = False

    for _ in range(n - 1):
        length = data[idx]
        idx += 1
        cur = data[idx:idx + length]
        idx += length

        p = 0
        limit = min(len(prev), len(cur))

        while p < limit and prev[p] == cur[p]:
            p += 1

        if p == limit:
            if len(prev) > len(cur):
                impossible = True
        else:
            a = prev[p]
            b = cur[p]

            if a < b:
                # Need: if b is large, then a must also be large.
                graph[b].append(a)
            else:
                # a > b: a must be large and b must be small.
                must_be_large[a] = True
                must_be_small[b] = True

        prev = cur

    if impossible:
        sys.stdout.write("No\n")
        return

    reachable_large = must_be_large[:]
    queue = deque()

    for letter in range(1, m + 1):
        if reachable_large[letter]:
            queue.append(letter)

    while queue:
        v = queue.popleft()
        for u in graph[v]:
            if not reachable_large[u]:
                reachable_large[u] = True
                queue.append(u)

    for letter in range(1, m + 1):
        if must_be_small[letter] and reachable_large[letter]:
            sys.stdout.write("No\n")
            return

    answer = [letter for letter in range(1, m + 1) if reachable_large[letter]]

    output = ["Yes", str(len(answer))]
    if answer:
        output.append(" ".join(map(str, answer)))

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    solve()