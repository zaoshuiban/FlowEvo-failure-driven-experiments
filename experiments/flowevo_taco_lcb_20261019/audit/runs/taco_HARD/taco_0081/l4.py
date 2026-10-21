import sys


def ints():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False
    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False
    if in_num:
        yield num


def solve() -> None:
    it = ints()
    try:
        n = next(it)
        m = next(it)
    except StopIteration:
        return

    # cap[x] = 1  -> letter x must be large
    # cap[x] = 0  -> letter x must stay small
    # cap[x] = -1 -> not forced yet
    cap = [-1] * (m + 1)

    # For x < y at the first differing position, the only forbidden state is
    # x small and y large. Therefore, if y is large, x must be large.
    # Edge y -> x means: y large => x large.
    adj = [[] for _ in range(m + 1)]

    impossible = False
    prev = None

    for _ in range(n):
        length = next(it)
        cur = [next(it) for _ in range(length)]

        if prev is not None and not impossible:
            limit = min(len(prev), len(cur))
            j = 0
            while j < limit and prev[j] == cur[j]:
                j += 1

            if j == limit:
                # If the previous word is longer, the current word is its
                # proper prefix, so previous > current, which is not allowed.
                if len(prev) > len(cur):
                    impossible = True
            else:
                u = prev[j]
                v = cur[j]

                if u < v:
                    # Forbidden: u small and v large.
                    # Thus v large => u large.
                    adj[v].append(u)
                else:
                    # u > v: the only valid possibility is u large and v small.
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

    # Propagate forced large letters through implications.
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

    out = ["Yes", str(len(answer))]
    if answer:
        out.append(" ".join(map(str, answer)))

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    solve()