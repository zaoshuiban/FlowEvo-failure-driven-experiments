import sys

sys.setrecursionlimit(10000)


def next_lucky(s: str) -> str:
    s = s.lstrip('0') or '0'
    n = len(s)

    def dfs(i: int):
        if i == n:
            return None  # We matched s completely, so it is not strictly greater.

        c = s[i]

        for d in ('3', '5'):
            if d < c:
                continue

            if d == c:
                suffix = dfs(i + 1)
                if suffix is not None:
                    return d + suffix
            else:
                return d + '3' * (n - i - 1)

        return None

    answer = dfs(0)

    if answer is None:
        answer = '3' * (n + 1)

    return answer


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    results = []

    for i in range(1, t + 1):
        number = data[i].decode()
        results.append(next_lucky(number))

    sys.stdout.write('\n'.join(results))


if __name__ == "__main__":
    main()