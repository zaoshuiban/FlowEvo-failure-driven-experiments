import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    k = int(next(it))
    s = next(it)

    first = [-1] * n
    second = [-1] * n

    for j in range(k):
        c = int(next(it))
        for _ in range(c):
            x = int(next(it)) - 1
            if first[x] == -1:
                first[x] = j
            else:
                second[x] = j

    del data, it

    parent = list(range(k))
    parity = [0] * k          # value[node] xor value[parent[node]]
    size = [1] * k
    cnt0 = [1] * k            # variables in component with parity 0 from root
    cnt1 = [0] * k            # variables in component with parity 1 from root
    fixed = [-1] * k          # fixed value of root, -1 if unknown

    total = 0

    sys.setrecursionlimit(1_000_000)

    def find(x):
        if parent[x] != x:
            p = parent[x]
            r, w = find(p)
            parity[x] ^= w
            parent[x] = r
        return parent[x], parity[x]

    def cost(r):
        if fixed[r] == -1:
            return min(cnt0[r], cnt1[r])
        if fixed[r] == 0:
            return cnt1[r]
        return cnt0[r]

    def set_fixed(x, value):
        nonlocal total
        r, p = find(x)
        need_root_value = p ^ value

        if fixed[r] == -1:
            total -= cost(r)
            fixed[r] = need_root_value
            total += cost(r)

    def unite(x, y, relation):
        nonlocal total

        rx, px = find(x)
        ry, py = find(y)

        # value[x] xor value[y] = relation
        # value[rx] xor value[ry] = w
        w = relation ^ px ^ py

        if rx == ry:
            return

        total -= cost(rx) + cost(ry)

        if size[rx] < size[ry]:
            child, par = rx, ry
        else:
            child, par = ry, rx

        parent[child] = par
        parity[child] = w
        size[par] += size[child]

        if w == 0:
            cnt0[par] += cnt0[child]
            cnt1[par] += cnt1[child]
        else:
            cnt0[par] += cnt1[child]
            cnt1[par] += cnt0[child]

        child_fixed = fixed[child]
        if child_fixed != -1:
            expected_parent_value = child_fixed ^ w
            if fixed[par] == -1:
                fixed[par] = expected_parent_value

        fixed[child] = -1
        total += cost(par)

    answers = []

    for i in range(n):
        u = first[i]
        v = second[i]

        # Need: s[i] xor (xor of chosen subsets containing i) = 1
        target = 1 if s[i] == ord('0') else 0

        if u == -1 and v == -1:
            pass
        elif v == -1:
            set_fixed(u, target)
        else:
            unite(u, v, target)

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()