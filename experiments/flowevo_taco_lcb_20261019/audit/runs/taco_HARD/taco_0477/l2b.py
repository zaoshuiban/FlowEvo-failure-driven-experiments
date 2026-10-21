import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = [x - 1 for x in data[1:1 + n]]

    # Case 1: there is a fixed vertex. Use a star centered at it.
    fixed = -1
    for i in range(n):
        if p[i] == i:
            fixed = i
            break

    if fixed != -1:
        ans = ["YES"]
        for v in range(n):
            if v != fixed:
                ans.append(f"{fixed + 1} {v + 1}")
        sys.stdout.write("\n".join(ans))
        return

    # Case 2: no fixed point. We need all cycles to have even length
    # and at least one 2-cycle to use as the center edge.
    visited = [False] * n
    all_even = True
    center = None

    for i in range(n):
        if visited[i]:
            continue

        length = 0
        cur = i
        while not visited[cur]:
            visited[cur] = True
            length += 1
            cur = p[cur]

        if length % 2 == 1:
            all_even = False

        if length == 2 and center is None:
            center = (i, p[i])

    if not all_even or center is None:
        sys.stdout.write("NO")
        return

    a, b = center
    visited = [False] * n
    visited[a] = visited[b] = True

    edges = [(a, b)]

    for i in range(n):
        if visited[i]:
            continue

        cur = i
        parity = 0
        while not visited[cur]:
            visited[cur] = True

            if parity == 0:
                edges.append((a, cur))
            else:
                edges.append((b, cur))

            parity ^= 1
            cur = p[cur]

    ans = ["YES"]
    for u, v in edges:
        ans.append(f"{u + 1} {v + 1}")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()