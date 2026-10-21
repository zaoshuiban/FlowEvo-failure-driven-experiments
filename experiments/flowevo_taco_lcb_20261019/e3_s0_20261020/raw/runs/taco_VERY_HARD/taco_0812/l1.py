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

        q = data[idx:idx + m]
        idx += m

        first = [m] * (n + 1)
        last = [-1] * (n + 1)

        for i, x in enumerate(q):
            if first[x] == m:
                first[x] = i
            last[x] = i

        # arr[pos] = last occurrence of the number whose first occurrence is pos
        arr = [m] * m
        for value in range(1, n + 1):
            arr[first[value]] = last[value]

        # suff[i] = minimum last occurrence among values whose first occurrence >= i
        suff = [m] * (m + 1)
        for i in range(m - 1, -1, -1):
            suff[i] = min(arr[i], suff[i + 1])

        max_remaining = 0

        for left in range(m):
            remaining = suff[left] - left
            if remaining > max_remaining:
                max_remaining = remaining

        answers.append(str(m - max_remaining))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()