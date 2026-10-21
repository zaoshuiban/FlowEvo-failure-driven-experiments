import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        q = next(it)

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            u = next(it) - 1
            v = next(it) - 1
            adj[u].append(v)
            adj[v].append(u)

        parent = [-1] * n
        parity = [0] * n
        child_count = [0] * n

        parent[0] = -2
        order = [0]

        for u in order:
            for v in adj[u]:
                if v == parent[u]:
                    continue
                parent[v] = u
                parity[v] = parity[u] ^ 1
                child_count[u] += 1
                order.append(v)

        if q == 1:
            total = 0
            for u in range(n):
                if parity[u] == 0:
                    total += abs(1 - child_count[u])
            answers.append(str(total))

        else:
            total = 0
            freq = {}

            for u in range(n):
                if parity[u] == 0:
                    b = abs(1 - child_count[u])
                    total += b
                    if b > 0:
                        freq[b] = freq.get(b, 0) + 1

            if total == 0:
                answers.append("0")
                continue

            reachable = 1

            for value, count in freq.items():
                take = 1
                while count > 0:
                    use = min(take, count)
                    reachable |= reachable << (value * use)
                    count -= use
                    take <<= 1

            half = total // 2
            mask = (1 << (half + 1)) - 1
            best = (reachable & mask).bit_length() - 1

            answers.append(str(total - 2 * best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()