import sys


def add_one(s: str) -> str:
    a = list(s)
    i = len(a) - 1

    while i >= 0 and a[i] == '9':
        a[i] = '0'
        i -= 1

    if i >= 0:
        a[i] = chr(ord(a[i]) + 1)
        return ''.join(a)

    return '1' + ''.join(a)


def smallest_lucky_ge(t: str):
    n = len(t)

    def dfs(i: int, greater: bool):
        if i == n:
            return ""

        if greater:
            return '3' * (n - i)

        c = t[i]

        if c <= '3':
            if c == '3':
                res = dfs(i + 1, False)
                if res is not None:
                    return '3' + res
            else:
                return '3' + '3' * (n - i - 1)

            return '5' + '3' * (n - i - 1)

        elif c <= '5':
            if c == '5':
                res = dfs(i + 1, False)
                if res is not None:
                    return '5' + res
                return None
            else:
                return '5' + '3' * (n - i - 1)

        else:
            return None

    return dfs(0, False)


def next_lucky(number: str) -> str:
    s = number.lstrip('0') or '0'
    target = add_one(s)

    ans = smallest_lucky_ge(target)
    if ans is None:
        ans = '3' * (len(target) + 1)

    return ans


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = data[i].decode()
        answers.append(next_lucky(n))

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    main()