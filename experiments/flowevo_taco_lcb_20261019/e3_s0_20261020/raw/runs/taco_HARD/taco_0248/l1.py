import sys

MOD = 1_000_000_007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    parent = [0] * (n + 1)
    children = [[] for _ in range(n + 1)]

    idx = 1
    for i in range(2, n + 1):
        p = int(data[idx])
        idx += 1
        parent[i] = p
        children[p].append(i)

    # down[v] = product over children c of (1 + down[c])
    down = [1] * (n + 1)

    for v in range(n, 1, -1):
        factor = down[v] + 1
        if factor >= MOD:
            factor -= MOD
        down[parent[v]] = down[parent[v]] * factor % MOD

    # up[v] is the corresponding DP value from parent side to v
    up = [0] * (n + 1)

    for p in range(1, n + 1):
        ch = children[p]
        k = len(ch)
        if k == 0:
            continue

        base = 1 if p == 1 else up[p] + 1
        if base >= MOD:
            base -= MOD

        if k == 1:
            up[ch[0]] = base
            continue

        prefix = [1] * (k + 1)
        for j, c in enumerate(ch):
            factor = down[c] + 1
            if factor >= MOD:
                factor -= MOD
            prefix[j + 1] = prefix[j] * factor % MOD

        suffix = 1
        for j in range(k - 1, -1, -1):
            c = ch[j]
            up[c] = base * prefix[j] % MOD * suffix % MOD

            factor = down[c] + 1
            if factor >= MOD:
                factor -= MOD
            suffix = suffix * factor % MOD

    answer = []
    for v in range(1, n + 1):
        if v == 1:
            value = down[v]
        else:
            factor = up[v] + 1
            if factor >= MOD:
                factor -= MOD
            value = down[v] * factor % MOD

        answer.append(str(value))

    sys.stdout.write(" ".join(answer))


if __name__ == "__main__":
    main()