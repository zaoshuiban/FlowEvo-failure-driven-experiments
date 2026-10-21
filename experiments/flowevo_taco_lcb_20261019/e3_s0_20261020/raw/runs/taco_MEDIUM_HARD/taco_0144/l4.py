import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    pos = 1
    output = []

    for _ in range(t):
        n = int(data[pos])
        pos += 1

        if n == 1:
            output.append(b"0")
            continue

        next_city = {}
        indegree = {}
        total_cost = 0

        for _ in range(n - 1):
            a = data[pos]
            b = data[pos + 1]
            c = data[pos + 2]
            pos += 3

            next_city[a] = (b, c)
            indegree[b] = indegree.get(b, 0) + 1

            if a not in indegree:
                indegree[a] = 0

            total_cost += int(c)

        start = None
        for city, degree in indegree.items():
            if degree == 0:
                start = city
                break

        current = start
        for _ in range(n - 1):
            nxt, cost = next_city[current]
            output.append(current + b" " + nxt + b" " + cost)
            current = nxt

        output.append(str(total_cost).encode())

    sys.stdout.buffer.write(b"\n".join(output))
    if output:
        sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    solve()