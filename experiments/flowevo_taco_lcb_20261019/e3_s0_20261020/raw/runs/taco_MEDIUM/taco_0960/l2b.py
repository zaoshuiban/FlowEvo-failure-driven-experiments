import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        p = data[idx:idx + n]
        idx += n

        pos = [0] * (n + 1)
        for i, value in enumerate(p):
            pos[value] = i

        bad_pref = [0] * (n + 1)
        for value in range(1, n):
            bad_pref[value] = bad_pref[value - 1] + (
                1 if pos[value] > pos[value + 1] else 0
            )

        def can(k: int) -> bool:
            left = k + 1
            right = n - k

            if left >= right:
                return True

            return bad_pref[right - 1] - bad_pref[left - 1] == 0

        low, high = 0, n // 2

        while low < high:
            mid = (low + high) // 2
            if can(mid):
                high = mid
            else:
                low = mid + 1

        answers.append(str(low))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()