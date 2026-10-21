import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        w = [next(it) for _ in range(n)]

        prefix_pos = {0: 0}
        current_sum = 0

        for i, weight in enumerate(w, 1):
            current_sum += weight
            prefix_pos[current_sum] = i

        suffix_sum = 0
        best = 0

        for suffix_count in range(n + 1):
            prefix_count = prefix_pos.get(suffix_sum)

            if prefix_count is not None and prefix_count + suffix_count <= n:
                best = max(best, prefix_count + suffix_count)

            if suffix_count < n:
                suffix_sum += w[n - 1 - suffix_count]

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()