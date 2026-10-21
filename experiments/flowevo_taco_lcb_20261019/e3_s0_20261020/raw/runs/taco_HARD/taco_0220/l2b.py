import sys
from collections import Counter, defaultdict


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    arr = data[1:1 + 2 * n]

    counter = Counter(arr)
    items = list(counter.items())
    m = len(items)

    # dp[used][distinct_first] = maximum distinct values in the second heap
    dp = [[-1] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0

    parent_used = []
    parent_taken = []

    for value, count in items:
        ndp = [[-1] * (m + 1) for _ in range(n + 1)]
        par_used = [[-1] * (m + 1) for _ in range(n + 1)]
        par_taken = [[-1] * (m + 1) for _ in range(n + 1)]

        for used in range(n + 1):
            for distinct_first in range(m + 1):
                cur = dp[used][distinct_first]
                if cur < 0:
                    continue

                # Put all cubes with this value into the second heap.
                if cur + 1 > ndp[used][distinct_first]:
                    ndp[used][distinct_first] = cur + 1
                    par_used[used][distinct_first] = used
                    par_taken[used][distinct_first] = 0

                new_distinct_first = distinct_first + 1

                # Put all cubes with this value into the first heap.
                new_used = used + count
                if (
                    new_used <= n
                    and new_distinct_first <= m
                    and cur > ndp[new_used][new_distinct_first]
                ):
                    ndp[new_used][new_distinct_first] = cur
                    par_used[new_used][new_distinct_first] = used
                    par_taken[new_used][new_distinct_first] = count

                # Split cubes with this value between both heaps.
                if count >= 2 and new_distinct_first <= m:
                    max_take = min(count - 1, n - used)
                    for take in range(1, max_take + 1):
                        new_used = used + take
                        if cur + 1 > ndp[new_used][new_distinct_first]:
                            ndp[new_used][new_distinct_first] = cur + 1
                            par_used[new_used][new_distinct_first] = used
                            par_taken[new_used][new_distinct_first] = take

        dp = ndp
        parent_used.append(par_used)
        parent_taken.append(par_taken)

    best_answer = -1
    best_distinct_first = -1

    for distinct_first in range(m + 1):
        distinct_second = dp[n][distinct_first]
        if distinct_second >= 0:
            answer = distinct_first * distinct_second
            if answer > best_answer:
                best_answer = answer
                best_distinct_first = distinct_first

    chosen_first_count = [0] * m

    used = n
    distinct_first = best_distinct_first

    for i in range(m - 1, -1, -1):
        take = parent_taken[i][used][distinct_first]
        chosen_first_count[i] = take

        previous_used = parent_used[i][used][distinct_first]
        if take > 0:
            distinct_first -= 1
        used = previous_used

    positions = defaultdict(list)
    for index, value in enumerate(arr):
        positions[value].append(index)

    answer_labels = ['2'] * (2 * n)

    for i, (value, count) in enumerate(items):
        take = chosen_first_count[i]
        for j, index in enumerate(positions[value]):
            if j < take:
                answer_labels[index] = '1'
            else:
                answer_labels[index] = '2'

    print(best_answer)
    print(' '.join(answer_labels))


if __name__ == "__main__":
    solve()