import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []
    INF = 10**9

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

        # min_last_at_first[p] = minimum last occurrence among values
        # whose first occurrence is at position p
        min_last_at_first = [INF] * (m + 2)

        for value in range(1, n + 1):
            p = first[value]
            if last[value] < min_last_at_first[p]:
                min_last_at_first[p] = last[value]

        # suffix_min[L + 1] gives the minimum last occurrence among values
        # whose first occurrence is greater than L
        suffix_min = [INF] * (m + 2)

        for i in range(m, 0, -1):
            suffix_min[i] = min(min_last_at_first[i], suffix_min[i + 1])

        answer = m

        for prefix_len in range(m + 1):
            g = suffix_min[prefix_len + 1]

            if g == INF:
                cost = prefix_len
            else:
                required_suffix = m - g + 1
                cost = prefix_len + required_suffix

            if cost < answer:
                answer = cost

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()