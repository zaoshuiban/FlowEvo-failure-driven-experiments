import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[] for _ in range(m + 1)]
    fixed_true = [False] * (m + 1)
    fixed_false = [False] * (m + 1)

    possible = True
    prev = None

    for idx in range(n):
        length = next(it)
        curr = [next(it) for _ in range(length)]

        if idx > 0:
            common = min(len(prev), length)
            pos = 0

            while pos < common and prev[pos] == curr[pos]:
                pos += 1

            if pos == common:
                if len(prev) > length:
                    possible = False
            else:
                a = prev[pos]
                b = curr[pos]

                if a < b:
                    # If b is large, a must also be large.
                    adj[b].append(a)
                else:
                    # Need a large and b small.
                    fixed_true[a] = True
                    fixed_false[b] = True

        prev = curr

    if not possible:
        sys.stdout.write("No\n")
        return

    forced = fixed_true[:]
    q = deque()

    for v in range(1, m + 1):
        if forced[v]:
            q.append(v)

    while q and possible:
        v = q.popleft()

        if fixed_false[v]:
            possible = False
            break

        for to in adj[v]:
            if not forced[to]:
                forced[to] = True
                q.append(to)

    if not possible:
        sys.stdout.write("No\n")
        return

    answer = [str(v) for v in range(1, m + 1) if forced[v]]
    result = ["Yes", str(len(answer)), " ".join(answer), ""]
    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    solve()