import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ptr = 1
    output = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        b = data[ptr:ptr + n]
        ptr += n

        size = n + 2  # indices 0 ... n+1
        buckets = [[] for _ in range(size)]
        has = [0] * size

        for value, parent in enumerate(b, start=1):
            buckets[parent].append(value)
            has[parent] += 1

        if has[0] > 0:
            start = 0
            current_is_small = False
        else:
            start = n + 1
            current_is_small = True

        permutation = []
        small_count = 0
        cur = start

        while cur != -1:
            elems = buckets[cur]

            nxt = -1
            for x in elems:
                if has[x] > 0:
                    nxt = x
                    break

            if current_is_small:
                small_count += len(elems)

            for x in elems:
                if x != nxt:
                    permutation.append(x)

            if nxt != -1:
                permutation.append(nxt)

            current_is_small = not current_is_small
            cur = nxt

        k = small_count
        output.append(str(k))
        output.append(" ".join(map(str, permutation)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()