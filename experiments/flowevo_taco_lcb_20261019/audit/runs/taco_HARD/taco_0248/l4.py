import sys

MOD = 1_000_000_007

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    children = [[] for _ in range(n + 1)]

    # p_i is given for i = 2..n, and p_i < i.
    for i in range(2, n + 1):
        p = data[i - 1]
        children[p].append(i)

    # down[v] = number of valid choices inside v's subtree,
    # excluding the edge from v to its parent.
    down = [1] * (n + 1)

    for v in range(n, 0, -1):
        product = 1
        for u in children[v]:
            product = product * (down[u] + 1) % MOD
        down[v] = product

    # up[v] = number of valid choices in the component on the parent side
    # after removing the edge between v and its parent.
    up = [0] * (n + 1)
    answer = [0] * (n + 1)

    for v in range(1, n + 1):
        parent_factor = up[v] + 1
        if parent_factor >= MOD:
            parent_factor -= MOD

        answer[v] = down[v] * parent_factor % MOD

        ch = children[v]
        m = len(ch)
        if m == 0:
            continue

        prefix = [1] * (m + 1)
        for i, u in enumerate(ch):
            prefix[i + 1] = prefix[i] * (down[u] + 1) % MOD

        suffix = 1
        for i in range(m - 1, -1, -1):
            u = ch[i]
            up[u] = parent_factor * prefix[i] % MOD * suffix % MOD
            suffix = suffix * (down[u] + 1) % MOD

    sys.stdout.write(" ".join(str(answer[i]) for i in range(1, n + 1)) + "\n")


if __name__ == "__main__":
    solve()