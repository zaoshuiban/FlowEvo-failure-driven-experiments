import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    left = [0] * n
    right = [0] * n

    idx = 1
    for i in range(n):
        left[i] = data[idx]
        right[i] = data[idx + 1]
        idx += 2

    INF = 10**18

    pref_max_left = [-1] * (n + 1)
    pref_min_right = [INF] * (n + 1)

    for i in range(n):
        pref_max_left[i + 1] = max(pref_max_left[i], left[i])
        pref_min_right[i + 1] = min(pref_min_right[i], right[i])

    suff_max_left = [-1] * (n + 1)
    suff_min_right = [INF] * (n + 1)

    for i in range(n - 1, -1, -1):
        suff_max_left[i] = max(suff_max_left[i + 1], left[i])
        suff_min_right[i] = min(suff_min_right[i + 1], right[i])

    answer = 0

    for i in range(n):
        max_left = max(pref_max_left[i], suff_max_left[i + 1])
        min_right = min(pref_min_right[i], suff_min_right[i + 1])

        answer = max(answer, min_right - max_left)

    print(answer)


if __name__ == "__main__":
    solve()