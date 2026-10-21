import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        b = [next(it) for _ in range(n)]

        groups = [[] for _ in range(n + 2)]

        # k must satisfy:
        # if b_x == 0: x > k
        # if b_x == n + 1: x <= k
        # otherwise: exactly one of x and b_x is <= k
        low = 0
        high = n

        for x, p in enumerate(b, start=1):
            groups[p].append(x)

            if p == 0:
                high = min(high, x - 1)
            elif p == n + 1:
                low = max(low, x)
            else:
                l = min(x, p)
                r = max(x, p)
                low = max(low, l)
                high = min(high, r - 1)

        k = low

        if groups[0]:
            cur = 0
        else:
            cur = n + 1

        permutation = []

        while True:
            group = groups[cur]
            if not group:
                break

            nxt = -1
            for v in group:
                if groups[v]:
                    nxt = v
                    break

            if nxt == -1:
                permutation.extend(group)
                break

            for v in group:
                if v != nxt:
                    permutation.append(v)
            permutation.append(nxt)

            cur = nxt

        answers.append(str(k))
        answers.append(" ".join(map(str, permutation)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()