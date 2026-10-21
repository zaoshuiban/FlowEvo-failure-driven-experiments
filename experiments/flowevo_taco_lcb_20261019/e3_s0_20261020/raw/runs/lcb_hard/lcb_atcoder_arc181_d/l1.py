import sys
from bisect import bisect_left


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    P = [next(it) for _ in range(N)]

    M = next(it)
    A = [next(it) for _ in range(M)]

    bit = [0] * (N + 2)

    def add(i):
        while i <= N:
            bit[i] += 1
            i += i & -i

    def prefix_sum(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    pos = [0] * (N + 1)
    larger_left = [0] * (N + 1)

    initial_inv = 0

    for i, v in enumerate(P, 1):
        pos[v] = i
        less_count = prefix_sum(v)
        greater_count = (i - 1) - less_count
        larger_left[v] = greater_count
        initial_inv += greater_count
        add(v)

    diff = [0] * (M + 3)

    for v in range(1, N + 1):
        cnt = larger_left[v]
        if cnt == 0:
            continue

        idx = bisect_left(A, pos[v])
        if idx == M:
            continue

        start = idx + 1
        diff[start] += 1

        end = start + cnt
        if end <= M:
            diff[end] -= 1

    active = 0
    removed = 0
    answers = []

    for t in range(1, M + 1):
        active += diff[t]
        removed += active
        answers.append(str(initial_inv - removed))

    print("\n".join(answers))


if __name__ == "__main__":
    main()