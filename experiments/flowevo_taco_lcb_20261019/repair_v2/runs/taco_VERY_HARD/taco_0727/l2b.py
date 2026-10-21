import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        q = next(it)

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next(it)
            v = next(it)
            adj[u].append(v)
            adj[v].append(u)

        parent = [0] * (n + 1)
        depth = [0] * (n + 1)
        parent[1] = -1

        order = [1]
        for v in order:
            next_depth = depth[v] + 1
            for u in adj[v]:
                if u != parent[v]:
                    parent[u] = v
                    depth[u] = next_depth
                    order.append(u)

        total_weight = 0
        freq = {}

        for v in range(1, n + 1):
            if (depth[v] & 1) == 0:
                children = len(adj[v]) - (0 if v == 1 else 1)
                coefficient = 1 - children
                weight = abs(coefficient)

                if weight:
                    total_weight += weight
                    if q == 2:
                        freq[weight] = freq.get(weight, 0) + 1

        if q == 1:
            answers.append(str(total_weight))
        else:
            if total_weight == 0:
                answers.append("0")
                continue

            bits = 1

            for weight, count in freq.items():
                power = 1
                while count > 0:
                    take = min(power, count)
                    shift = weight * take
                    bits |= bits << shift
                    count -= take
                    power <<= 1

            half = total_weight // 2
            mask = (1 << (half + 1)) - 1
            best = (bits & mask).bit_length() - 1

            min_value = total_weight - 2 * best
            answers.append(str(min_value))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()