import sys

MOD = 1_000_000_007

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    children = [[] for _ in range(n + 1)]

    idx = 1
    for city in range(2, n + 1):
        parent = data[idx]
        idx += 1
        children[parent].append(city)

    dp = [0] * (n + 1)

    # dp[v] = number of valid antichains inside the subtree of v,
    # considering v as the parent side.
    for v in range(n, 0, -1):
        product = 1
        for child in children[v]:
            product = product * (dp[child] + 1) % MOD
        dp[v] = product

    up = [0] * (n + 1)
    answer = [0] * (n + 1)

    for v in range(1, n + 1):
        if v == 1:
            answer[v] = dp[v]
            base = 1
        else:
            parent_side = up[v] + 1
            if parent_side >= MOD:
                parent_side -= MOD
            answer[v] = dp[v] * parent_side % MOD
            base = parent_side

        ch = children[v]
        m = len(ch)

        if m == 0:
            continue

        prefix = [1] * (m + 1)
        for i in range(m):
            child = ch[i]
            prefix[i + 1] = prefix[i] * (dp[child] + 1) % MOD

        suffix = 1
        for i in range(m - 1, -1, -1):
            child = ch[i]
            up[child] = base * prefix[i] % MOD * suffix % MOD
            suffix = suffix * (dp[child] + 1) % MOD

    sys.stdout.write(" ".join(str(answer[i]) for i in range(1, n + 1)))


if __name__ == "__main__":
    solve()