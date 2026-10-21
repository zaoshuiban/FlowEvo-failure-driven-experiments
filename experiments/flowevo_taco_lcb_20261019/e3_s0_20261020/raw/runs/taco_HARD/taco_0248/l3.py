import sys

MOD = 1_000_000_007

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    children = [[] for _ in range(n + 1)]

    for city in range(2, n + 1):
        parent = data[city - 1]
        children[parent].append(city)

    # down[v] = number of valid antichains of bad edges inside v's subtree,
    # excluding the edge from v to its parent.
    down = [1] * (n + 1)

    for v in range(n, 0, -1):
        product = 1
        for child in children[v]:
            product = product * (down[child] + 1) % MOD
        down[v] = product

    # up[v] = number of valid antichains in the component on the parent side
    # after removing the edge between v and its parent.
    up = [0] * (n + 1)
    answer = [0] * (n + 1)

    for v in range(1, n + 1):
        if v == 1:
            answer[v] = down[v]
            parent_factor = 1
        else:
            parent_factor = up[v] + 1
            if parent_factor >= MOD:
                parent_factor -= MOD
            answer[v] = down[v] * parent_factor % MOD

        ch = children[v]
        m = len(ch)
        if m == 0:
            continue

        prefix = [1] * (m + 1)
        for i in range(m):
            child = ch[i]
            prefix[i + 1] = prefix[i] * (down[child] + 1) % MOD

        suffix = 1
        for i in range(m - 1, -1, -1):
            child = ch[i]
            up[child] = parent_factor * prefix[i] % MOD * suffix % MOD
            suffix = suffix * (down[child] + 1) % MOD

    sys.stdout.write(" ".join(str(answer[i]) for i in range(1, n + 1)) + "\n")


if __name__ == "__main__":
    solve()