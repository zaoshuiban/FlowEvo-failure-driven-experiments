import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        q = data[idx + 1]
        idx += 2

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = data[idx]
            v = data[idx + 1]
            idx += 2
            adj[u].append(v)
            adj[v].append(u)

        parity = [0] * (n + 1)
        parent = [0] * (n + 1)
        child_count = [0] * (n + 1)

        parent[1] = -1
        order = [1]

        for v in order:
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                parity[u] = parity[v] ^ 1
                child_count[v] += 1
                order.append(u)

        counts = {}
        total_weight = 0

        for v in range(1, n + 1):
            if parity[v] == 0:
                k = child_count[v]
                coef = 1 - k

                if coef > 0:
                    total_weight += coef
                    counts[1] = counts.get(1, 0) + coef
                elif coef < 0:
                    weight = -coef
                    total_weight += weight
                    counts[weight] = counts.get(weight, 0) + 1

        if q == 1:
            answers.append(str(total_weight))
        else:
            bits = 1

            for weight, cnt in counts.items():
                power = 1
                while cnt > 0:
                    take = min(power, cnt)
                    bits |= bits << (weight * take)
                    cnt -= take
                    power <<= 1

            target = total_weight // 2
            mask = (1 << (target + 1)) - 1
            best = (bits & mask).bit_length() - 1
            answer = total_weight - 2 * best

            answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()