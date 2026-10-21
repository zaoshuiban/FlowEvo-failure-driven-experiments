import sys
from collections import Counter, defaultdict


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    arr = data[1:1 + 2 * n]

    freq = Counter(arr)
    items = list(freq.items())  # (value, count)
    m = len(items)

    NEG = -10**9

    # dp[used_first][distinct_first] = maximum distinct values in the second heap
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0

    # choices[i][used][distinct_first] stores how many copies of items[i]
    # were put into the first heap for this DP state.
    choices = []

    for _, count in items:
        ndp = [[NEG] * (m + 1) for _ in range(n + 1)]
        choice = [[-1] * (m + 1) for _ in range(n + 1)]

        for used in range(n + 1):
            for distinct_first in range(m + 1):
                cur = dp[used][distinct_first]
                if cur < 0:
                    continue

                # Put all copies into the second heap.
                if cur + 1 > ndp[used][distinct_first]:
                    ndp[used][distinct_first] = cur + 1
                    choice[used][distinct_first] = 0

                new_distinct_first = distinct_first + 1
                if new_distinct_first > m:
                    continue

                # Put all copies into the first heap.
                new_used = used + count
                if new_used <= n and cur > ndp[new_used][new_distinct_first]:
                    ndp[new_used][new_distinct_first] = cur
                    choice[new_used][new_distinct_first] = count

                # Split copies between both heaps.
                if count >= 2:
                    max_take = min(count - 1, n - used)
                    for take in range(1, max_take + 1):
                        new_used = used + take
                        if cur + 1 > ndp[new_used][new_distinct_first]:
                            ndp[new_used][new_distinct_first] = cur + 1
                            choice[new_used][new_distinct_first] = take

        dp = ndp
        choices.append(choice)

    best_answer = -1
    best_distinct_first = 0

    for distinct_first in range(m + 1):
        distinct_second = dp[n][distinct_first]
        if distinct_second >= 0:
            answer = distinct_first * distinct_second
            if answer > best_answer:
                best_answer = answer
                best_distinct_first = distinct_first

    # Reconstruct how many copies of each value go to the first heap.
    used = n
    distinct_first = best_distinct_first
    chosen_first_count = [0] * m

    for i in range(m - 1, -1, -1):
        take = choices[i][used][distinct_first]
        chosen_first_count[i] = take

        used -= take
        if take > 0:
            distinct_first -= 1

    positions = defaultdict(list)
    for index, value in enumerate(arr):
        positions[value].append(index)

    answer_labels = ['2'] * (2 * n)

    for i, (value, _) in enumerate(items):
        take = chosen_first_count[i]
        for index in positions[value][:take]:
            answer_labels[index] = '1'

    print(best_answer)
    print(' '.join(answer_labels))


if __name__ == "__main__":
    solve()