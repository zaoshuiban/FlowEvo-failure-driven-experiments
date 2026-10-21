import sys

def solve():
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    t = int(tokens[0])
    idx = 1
    output = []

    for _ in range(t):
        n = int(tokens[idx])
        idx += 1

        if n == 1:
            output.append("0")
            continue

        next_city = {}
        indegree = {}
        total_cost = 0

        for _ in range(n - 1):
            a = tokens[idx].decode()
            b = tokens[idx + 1].decode()
            c_str = tokens[idx + 2].decode()
            c = int(c_str)
            idx += 3

            next_city[a] = (b, c_str)
            indegree[b] = indegree.get(b, 0) + 1

            if a not in indegree:
                indegree[a] = 0

            total_cost += c

        start = None
        for city, degree in indegree.items():
            if degree == 0:
                start = city
                break

        current = start

        for _ in range(n - 1):
            nxt, cost_str = next_city[current]
            output.append(f"{current} {nxt} {cost_str}")
            current = nxt

        output.append(str(total_cost))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()