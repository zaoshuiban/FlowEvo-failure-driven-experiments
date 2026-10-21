import sys

def solve() -> None:
    sys.setrecursionlimit(1_000_000)
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    N = data[idx]
    idx += 1

    X = data[idx:idx + N]
    idx += N

    Q = data[idx]
    idx += 1

    # z_i = position_i - i (0-indexed)
    A = [X[i] - i for i in range(N)]

    INF = 10**18
    size = 4 * N + 5
    seg_sum = [0] * size
    seg_max = [0] * size
    lazy = [INF] * size

    def build(node: int, left: int, right: int) -> None:
        if left == right:
            v = A[left]
            seg_sum[node] = v
            seg_max[node] = v
            return

        mid = (left + right) // 2
        lc = node * 2
        build(lc, left, mid)
        build(lc + 1, mid + 1, right)

        seg_sum[node] = seg_sum[lc] + seg_sum[lc + 1]
        seg_max[node] = max(seg_max[lc], seg_max[lc + 1])

    def push(node: int, left: int, right: int) -> None:
        v = lazy[node]
        if v == INF:
            return

        lc = node * 2
        mid = (left + right) // 2

        if left != right:
            seg_sum[lc] = v * (mid - left + 1)
            seg_max[lc] = v
            lazy[lc] = v

            rc = lc + 1
            seg_sum[rc] = v * (right - mid)
            seg_max[rc] = v
            lazy[rc] = v

        lazy[node] = INF

    def range_assign(node: int, left: int, right: int,
                     ql: int, qr: int, value: int) -> int:
        if ql <= left and right <= qr:
            old_sum = seg_sum[node]
            seg_sum[node] = value * (right - left + 1)
            seg_max[node] = value
            lazy[node] = value
            return old_sum

        push(node, left, right)

        mid = (left + right) // 2
        lc = node * 2
        old_sum = 0

        if ql <= mid:
            old_sum += range_assign(lc, left, mid, ql, qr, value)
        if qr > mid:
            old_sum += range_assign(lc + 1, mid + 1, right, ql, qr, value)

        seg_sum[node] = seg_sum[lc] + seg_sum[lc + 1]
        seg_max[node] = max(seg_max[lc], seg_max[lc + 1])
        return old_sum

    def point_value(node: int, left: int, right: int, pos: int) -> int:
        if left == right:
            return seg_sum[node]

        push(node, left, right)
        mid = (left + right) // 2

        if pos <= mid:
            return point_value(node * 2, left, mid, pos)
        else:
            return point_value(node * 2 + 1, mid + 1, right, pos)

    def lower_bound_ge(threshold: int) -> int:
        if seg_max[1] < threshold:
            return N

        node = 1
        left = 0
        right = N - 1

        while left < right:
            push(node, left, right)
            mid = (left + right) // 2
            lc = node * 2

            if seg_max[lc] >= threshold:
                node = lc
                right = mid
            else:
                node = lc + 1
                left = mid + 1

        return left

    build(1, 0, N - 1)

    answer = 0

    for _ in range(Q):
        T = data[idx]
        G = data[idx + 1]
        idx += 2

        pos = T - 1
        target = G - pos

        current = point_value(1, 0, N - 1, pos)

        if current < target:
            first_ge = lower_bound_ge(target)
            right = first_ge - 1

            old_sum = range_assign(1, 0, N - 1, pos, right, target)
            answer += target * (right - pos + 1) - old_sum

        elif current > target:
            left = lower_bound_ge(target + 1)

            old_sum = range_assign(1, 0, N - 1, left, pos, target)
            answer += old_sum - target * (pos - left + 1)

    print(answer)


if __name__ == "__main__":
    solve()