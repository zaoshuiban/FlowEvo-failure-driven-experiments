import sys


def find_assignment(req_top, req_bottom, arr):
    n = len(arr)
    caps = [0] * n
    for i, (cap, _) in enumerate(arr):
        caps[i] = cap

    neg_inf = -10**18
    suffix_max = [neg_inf] * (n + 1)
    suffix_idx = [-1] * (n + 1)

    for idx in range(n - 1, -1, -1):
        cap = caps[idx]
        need = (req_bottom + cap - 1) // cap
        value = idx + 1 - need

        if value >= suffix_max[idx + 1]:
            suffix_max[idx] = value
            suffix_idx[idx] = idx
        else:
            suffix_max[idx] = suffix_max[idx + 1]
            suffix_idx[idx] = suffix_idx[idx + 1]

    for k in range(1, n):
        if caps[k - 1] * k >= req_top:
            start_bottom = k
            if suffix_max[start_bottom] >= start_bottom:
                end_bottom = suffix_idx[start_bottom]
                return k, end_bottom

    return None


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, x1, x2 = data[0], data[1], data[2]
    capacities = data[3:3 + n]

    servers = [(capacities[i], i + 1) for i in range(n)]
    servers.sort(key=lambda x: x[0], reverse=True)

    result = find_assignment(x1, x2, servers)

    if result is not None:
        k1, end2 = result
        start2 = k1
        k2 = end2 - start2 + 1

        ans1 = [servers[i][1] for i in range(k1)]
        ans2 = [servers[i][1] for i in range(start2, end2 + 1)]
    else:
        result = find_assignment(x2, x1, servers)

        if result is None:
            sys.stdout.write("No\n")
            return

        k2, end1 = result
        start1 = k2
        k1 = end1 - start1 + 1

        ans2 = [servers[i][1] for i in range(k2)]
        ans1 = [servers[i][1] for i in range(start1, end1 + 1)]

    output = [
        "Yes",
        f"{k1} {k2}",
        " ".join(map(str, ans1)),
        " ".join(map(str, ans2))
    ]

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()