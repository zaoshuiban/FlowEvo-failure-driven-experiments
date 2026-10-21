import sys


def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        n = next(it)
    except StopIteration:
        return

    a = [next(it) for _ in range(n)]

    adj = [[] for _ in range(n)]
    for _ in range(n - 1):
        u = next(it) - 1
        v = next(it) - 1
        adj[u].append(v)
        adj[v].append(u)

    del it

    max_a = max(a)

    buckets = [[] for _ in range(max_a + 1)]
    for i, value in enumerate(a):
        buckets[value].append(i)

    # F[d] will first store the number of pairs whose path gcd is divisible by d.
    F = [0] * (max_a + 1)
    vis = [0] * n
    vertices = []

    for d in range(1, max_a + 1):
        vertices.clear()
        append_vertex = vertices.append

        # Activate all vertices whose value is divisible by d.
        for value in range(d, max_a + 1, d):
            bucket = buckets[value]
            if bucket:
                for v in bucket:
                    vis[v] = d
                    append_vertex(v)

        if not vertices:
            continue

        total = 0

        # Count pairs inside each connected component of active vertices.
        for start in vertices:
            if vis[start] == d:
                vis[start] = 0
                stack = [start]
                push = stack.append
                size = 1

                while stack:
                    u = stack.pop()
                    for v in adj[u]:
                        if vis[v] == d:
                            vis[v] = 0
                            size += 1
                            push(v)

                total += size * (size + 1) // 2

        F[d] = total

    # Möbius inversion over divisibility:
    # exact[d] = divisible_count[d] - sum(exact[multiple], multiple > d)
    for d in range(max_a, 0, -1):
        sub = 0
        for multiple in range(d + d, max_a + 1, d):
            sub += F[multiple]
        F[d] -= sub

    out = []
    for i in range(1, max_a + 1):
        if F[i] > 0:
            out.append(f"{i} {F[i]}")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()