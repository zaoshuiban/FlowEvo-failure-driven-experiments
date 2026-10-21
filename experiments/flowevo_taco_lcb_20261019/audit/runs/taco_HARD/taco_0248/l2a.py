import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    children = [[] for _ in range(n)]

    for i, p in enumerate(data[1:], start=1):
        p -= 1
        children[p].append(i)

    # f[v] = number of antichains inside v's rooted subtree,
    # assuming v itself is selectable.
    f = [0] * n
    for v in range(n - 1, -1, -1):
        prod = 1
        for c in children[v]:
            prod = prod * f[c] % MOD
        f[v] = (1 + prod) % MOD

    up = [0] * n
    ans = [0] * n

    for v in range(n):
        prod_children = 1
        for c in children[v]:
            prod_children = prod_children * f[c] % MOD

        if v == 0:
            ans[v] = prod_children
            parent_value = 1
        else:
            ans[v] = up[v] * prod_children % MOD
            parent_value = up[v]

        ch = children[v]
        m = len(ch)
        if m == 0:
            continue

        prefix = [1] * (m + 1)
        for i in range(m):
            prefix[i + 1] = prefix[i] * f[ch[i]] % MOD

        suffix = 1
        for i in range(m - 1, -1, -1):
            c = ch[i]
            prod_except = prefix[i] * suffix % MOD
            prod_except = prod_except * parent_value % MOD
            up[c] = (1 + prod_except) % MOD
            suffix = suffix * f[c] % MOD

    print(*ans)


if __name__ == "__main__":
    main()