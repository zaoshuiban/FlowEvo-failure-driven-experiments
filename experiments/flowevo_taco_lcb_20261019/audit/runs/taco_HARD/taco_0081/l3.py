import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    pos = 2

    # cap[x] = 1  -> letter x must be capitalized
    # cap[x] = 0  -> letter x must stay small
    # cap[x] = -1 -> not fixed
    cap = [-1] * (m + 1)

    # Edge v -> u means: if v is capitalized, then u must also be capitalized.
    adj = [[] for _ in range(m + 1)]

    impossible = False
    prev = None

    for i in range(n):
        length = data[pos]
        pos += 1
        cur = data[pos:pos + length]
        pos += length

        if i > 0 and not impossible:
            a, b = prev, cur
            limit = min(len(a), len(b))
            j = 0

            while j < limit and a[j] == b[j]:
                j += 1

            if j == limit:
                # If the previous word is longer, current is its prefix,
                # so previous > current is unavoidable.
                if len(a) > len(b):
                    impossible = True
            else:
                u = a[j]
                v = b[j]

                if u < v:
                    # Bad only when u is small and v is large.
                    # Therefore v capitalized => u capitalized.
                    adj[v].append(u)
                else:
                    # u > v: the only valid choice is u large and v small.
                    if cap[u] == 0:
                        impossible = True
                    else:
                        cap[u] = 1

                    if cap[v] == 1:
                        impossible = True
                    else:
                        cap[v] = 0

        prev = cur

    if impossible:
        sys.stdout.write("No\n")
        return

    # Propagate all forced capitalizations through implications.
    stack = [i for i in range(1, m + 1) if cap[i] == 1]

    while stack and not impossible:
        v = stack.pop()

        for u in adj[v]:
            if cap[u] == 0:
                impossible = True
                break

            if cap[u] == -1:
                cap[u] = 1
                stack.append(u)

    if impossible:
        sys.stdout.write("No\n")
        return

    answer = [i for i in range(1, m + 1) if cap[i] == 1]

    sys.stdout.write(
        "Yes\n"
        + str(len(answer))
        + "\n"
        + " ".join(map(str, answer))
        + "\n"
    )


if __name__ == "__main__":
    solve()