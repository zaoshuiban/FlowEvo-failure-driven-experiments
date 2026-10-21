import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    idx = 2

    # val[x] = 1 -> letter x is capitalized
    # val[x] = 0 -> letter x must stay small
    # val[x] = -1 -> not fixed yet
    val = [-1] * (m + 1)

    # Edge v -> u means: if v is capitalized, u must also be capitalized.
    adj = [[] for _ in range(m + 1)]

    bad = False
    prev = None

    for i in range(n):
        length = data[idx]
        idx += 1
        cur = data[idx:idx + length]
        idx += length

        if i > 0 and not bad:
            a, b = prev, cur
            limit = min(len(a), len(b))
            j = 0

            while j < limit and a[j] == b[j]:
                j += 1

            if j == limit:
                # If the previous word is longer, the current word is its prefix,
                # so it is impossible to have previous <= current.
                if len(a) > len(b):
                    bad = True
            else:
                u, v = a[j], b[j]

                if u < v:
                    # We must avoid: u is small and v is large.
                    # So if v is large, u must also be large.
                    adj[v].append(u)
                else:
                    # u > v: the only valid option is u large and v small.
                    if val[u] == 0:
                        bad = True
                    else:
                        val[u] = 1

                    if val[v] == 1:
                        bad = True
                    else:
                        val[v] = 0

        prev = cur

    if bad:
        sys.stdout.write("No\n")
        return

    # Propagate all forced capitalizations.
    stack = [i for i in range(1, m + 1) if val[i] == 1]

    while stack and not bad:
        v = stack.pop()

        for u in adj[v]:
            if val[u] == 0:
                bad = True
                break
            if val[u] == -1:
                val[u] = 1
                stack.append(u)

    if bad:
        sys.stdout.write("No\n")
        return

    answer = [i for i in range(1, m + 1) if val[i] == 1]

    sys.stdout.write(
        "Yes\n"
        + str(len(answer))
        + "\n"
        + " ".join(map(str, answer))
        + "\n"
    )


if __name__ == "__main__":
    solve()