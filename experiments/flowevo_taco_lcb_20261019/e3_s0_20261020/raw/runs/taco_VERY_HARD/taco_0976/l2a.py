import sys

MOD = 998244353
SHIFT = 11
MASK = (1 << SHIFT) - 1


def solve() -> None:
    data = sys.stdin.buffer
    n_line = data.readline()
    while n_line.strip() == b"":
        n_line = data.readline()

    n = int(n_line)
    total_edges = n * (n - 1) // 2

    # bucket[w] stores the edge with weight w as (u << SHIFT) | v
    bucket = [0] * (total_edges + 1)

    for i in range(n):
        row = []
        while len(row) < n:
            row.extend(map(int, data.readline().split()))

        for j in range(n):
            w = row[j]
            if i < j:
                bucket[w] = (i << SHIFT) | j

    parent = list(range(n))
    size = [1] * n
    internal_cnt = [0] * n
    comp_node = list(range(n))

    max_nodes = 2 * n + 5
    valid = [False] * max_nodes
    left = [-1] * max_nodes
    right = [-1] * max_nodes
    next_node = n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Kruskal reconstruction tree
    for w in range(1, total_edges + 1):
        code = bucket[w]
        u = code >> SHIFT
        v = code & MASK

        ru = find(u)
        rv = find(v)

        if ru == rv:
            internal_cnt[ru] += 1
            continue

        node_a = comp_node[ru]
        node_b = comp_node[rv]
        sz_a = size[ru]
        sz_b = size[rv]

        if internal_cnt[ru] == sz_a * (sz_a - 1) // 2:
            valid[node_a] = True
        if internal_cnt[rv] == sz_b * (sz_b - 1) // 2:
            valid[node_b] = True

        new_cnt = internal_cnt[ru] + internal_cnt[rv] + 1
        new_size = sz_a + sz_b

        new_node = next_node
        next_node += 1

        left[new_node] = node_a
        right[new_node] = node_b

        if sz_a < sz_b:
            parent[ru] = rv
            size[rv] = new_size
            internal_cnt[rv] = new_cnt
            comp_node[rv] = new_node
        else:
            parent[rv] = ru
            size[ru] = new_size
            internal_cnt[ru] = new_cnt
            comp_node[ru] = new_node

    root = find(0)
    root_node = comp_node[root]
    valid[root_node] = True

    # Tree DP:
    # dp[v][k] = number of valid partitions of leaves in subtree v into k groups
    dp_nodes = [None] * max_nodes

    for node in range(next_node):
        if node < n:
            # For a leaf, the only partition is the singleton group.
            dp_nodes[node] = [0, 1]
        else:
            a = dp_nodes[left[node]]
            b = dp_nodes[right[node]]

            res = [0] * (len(a) + len(b) - 1)

            for i, ai in enumerate(a):
                if ai == 0:
                    continue
                for j, bj in enumerate(b):
                    if bj:
                        res[i + j] = (res[i + j] + ai * bj) % MOD

            # If this component itself is a valid group, take all its vertices as one group.
            if valid[node]:
                res[1] += 1
                if res[1] >= MOD:
                    res[1] -= MOD

            dp_nodes[node] = res
            dp_nodes[left[node]] = None
            dp_nodes[right[node]] = None

    ans = dp_nodes[root_node]
    if len(ans) < n + 1:
        ans += [0] * (n + 1 - len(ans))

    print(" ".join(str(ans[k] % MOD) for k in range(1, n + 1)))


if __name__ == "__main__":
    solve()