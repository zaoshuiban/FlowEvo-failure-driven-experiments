import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    base = n + 1

    forbidden_internal = set()
    forbidden_one = bytearray(n + 1)

    idx = 3
    for _ in range(m):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        if a == 1:
            forbidden_one[b] = 1
        elif b == 1:
            forbidden_one[a] = 1
        else:
            if a > b:
                a, b = b, a
            forbidden_internal.add(a * base + b)

    unvisited = set(range(2, n + 1))

    components = 0
    total_allowed_to_one = 0
    bad_component = False

    while unvisited:
        start = unvisited.pop()
        stack = [start]
        q_comp = 0

        while stack:
            v = stack.pop()

            if forbidden_one[v] == 0:
                q_comp += 1

            if not unvisited:
                continue

            new_unvisited = set()

            for u in unvisited:
                if v < u:
                    key = v * base + u
                else:
                    key = u * base + v

                if key in forbidden_internal:
                    new_unvisited.add(u)
                else:
                    stack.append(u)

            unvisited = new_unvisited

        components += 1
        total_allowed_to_one += q_comp

        if q_comp == 0:
            bad_component = True

    if not bad_component and components <= k <= total_allowed_to_one:
        sys.stdout.write("possible\n")
    else:
        sys.stdout.write("impossible\n")


if __name__ == "__main__":
    solve()