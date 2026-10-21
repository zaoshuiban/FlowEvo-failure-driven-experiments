import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        first = [m + 1] * (n + 1)
        last = [0] * (n + 1)

        for pos in range(1, m + 1):
            value = data[idx]
            idx += 1

            if first[value] == m + 1:
                first[value] = pos
            last[value] = pos

        INF = m + 1

        # min_last[p] = minimum last occurrence among values whose first occurrence is p
        min_last = [INF] * (m + 2)

        for value in range(1, n + 1):
            p = first[value]
            if last[value] < min_last[p]:
                min_last[p] = last[value]

        # suffix_min[l] = minimum last occurrence among values whose first occurrence >= l
        suffix_min = [INF] * (m + 3)

        for i in range(m, 0, -1):
            suffix_min[i] = min(min_last[i], suffix_min[i + 1])

        max_kept = 0

        # Choose the left endpoint l of the kept contiguous segment.
        # The maximum possible right endpoint is suffix_min[l] - 1.
        for l in range(1, m + 1):
            r = suffix_min[l] - 1
            if r >= l:
                kept_len = r - l + 1
                if kept_len > max_kept:
                    max_kept = kept_len

        answers.append(str(m - max_kept))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()