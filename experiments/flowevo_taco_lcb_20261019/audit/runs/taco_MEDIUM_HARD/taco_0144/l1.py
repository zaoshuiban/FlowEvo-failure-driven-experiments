import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)
    T = int(next(it))
    output = []

    for _ in range(T):
        N = int(next(it))

        if N == 1:
            output.append("0")
            continue

        outgoing = {}
        indegree = {}

        for _ in range(N - 1):
            a = next(it)
            b = next(it)
            c = int(next(it))

            outgoing[a] = (b, c)
            indegree[b] = indegree.get(b, 0) + 1

        start = None
        for city in outgoing:
            if indegree.get(city, 0) == 0:
                start = city
                break

        current = start
        total_cost = 0

        for _ in range(N - 1):
            nxt, cost = outgoing[current]
            output.append(f"{current} {nxt} {cost}")
            total_cost += cost
            current = nxt

        output.append(str(total_cost))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()