import sys
from bisect import bisect_left


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    arr = data[2:2 + n]

    # Collect every value that can ever appear in the array.
    possible_values = list(arr)
    idx = 2 + n

    for _ in range(q):
        op = data[idx]
        idx += 1
        if op == 0:
            x = data[idx]
            y = data[idx + 1]
            idx += 2
            possible_values.append(y)
        else:
            v = data[idx]
            idx += 1

    values = sorted(set(possible_values))
    m = len(values)
    comp = {value: i + 1 for i, value in enumerate(values)}  # 1-based compression

    INF = n + 1

    size = 1
    while size <= m:
        size <<= 1

    seg = [INF] * (2 * size)
    base = size

    # Initially, store the position of each value.
    for pos, value in enumerate(arr, 1):
        ci = comp[value]
        seg[base + ci] = pos

    for i in range(size - 1, 0, -1):
        left = seg[i << 1]
        right = seg[i << 1 | 1]
        seg[i] = left if left < right else right

    answers = []
    idx = 2 + n

    for _ in range(q):
        op = data[idx]
        idx += 1

        if op == 0:
            x = data[idx]
            y = data[idx + 1]
            idx += 2

            old_value = arr[x - 1]

            # Remove old value.
            ci_old = comp[old_value]
            p = base + ci_old
            seg[p] = INF
            p >>= 1

            while p:
                left = seg[p << 1]
                right = seg[p << 1 | 1]
                seg[p] = left if left < right else right
                p >>= 1

            # Insert new value.
            arr[x - 1] = y
            ci_new = comp[y]
            p = base + ci_new
            seg[p] = x
            p >>= 1

            while p:
                left = seg[p << 1]
                right = seg[p << 1 | 1]
                seg[p] = left if left < right else right
                p >>= 1

        else:
            v = data[idx]
            idx += 1

            # First compressed value >= v.
            ci = bisect_left(values, v)

            if ci == m:
                answers.append("-1")
                continue

            # Query minimum position among compressed values ci+1 ... m.
            l = base + ci + 1
            r = base + m + 1
            res = INF

            while l < r:
                if l & 1:
                    if seg[l] < res:
                        res = seg[l]
                    l += 1

                if r & 1:
                    r -= 1
                    if seg[r] < res:
                        res = seg[r]

                l >>= 1
                r >>= 1

            if res == INF:
                answers.append("-1")
            else:
                answers.append(str(res))

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()