import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        b = [0] * (n + 1)
        for i in range(1, n + 1):
            b[i] = data[idx]
            idx += 1

        children = [[] for _ in range(n + 2)]

        low = 0
        high = n

        for x in range(1, n + 1):
            p = b[x]
            children[p].append(x)

            if p == 0:
                high = min(high, x - 1)
            elif p == n + 1:
                low = max(low, x)
            else:
                if p < x:
                    low = max(low, p)
                    high = min(high, x - 1)
                else:
                    low = max(low, x)
                    high = min(high, p - 1)

        k = low

        ans = []
        current = n + 1 if children[n + 1] else 0

        while True:
            cur_children = children[current]
            if not cur_children:
                break

            continuation = -1
            for x in cur_children:
                if children[x]:
                    continuation = x
                    break

            if continuation == -1:
                ans.extend(cur_children)
                break

            for x in cur_children:
                if x != continuation:
                    ans.append(x)

            ans.append(continuation)
            current = continuation

        output.append(str(k))
        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()