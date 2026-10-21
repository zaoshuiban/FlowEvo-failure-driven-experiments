import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    out = []

    for _ in range(t):
        n = next(it)
        b = [next(it) for _ in range(n)]

        # Find the maximum value that must be <= k.
        k = 0
        has_n_plus_one = False

        for i, bi in enumerate(b, 1):
            if bi == n + 1:
                has_n_plus_one = True
                if i > k:
                    k = i
            elif bi != 0:
                j = bi
                small = i if i < j else j
                if small > k:
                    k = small

        root = n + 1 if has_n_plus_one else 0

        children = [[] for _ in range(n + 2)]
        for value, parent in enumerate(b, 1):
            children[parent].append(value)

        a = []
        cur = root

        while True:
            nonleaf = -1

            for child in children[cur]:
                if children[child]:
                    nonleaf = child
                else:
                    a.append(child)

            if nonleaf == -1:
                break

            a.append(nonleaf)
            cur = nonleaf

        out.append(str(k))
        out.append(" ".join(map(str, a)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()