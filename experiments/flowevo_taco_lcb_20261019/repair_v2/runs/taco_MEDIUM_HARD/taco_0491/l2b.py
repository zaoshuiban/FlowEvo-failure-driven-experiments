import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]
        b = [next(it) for _ in range(n)]

        ans = 0

        for bit in range(29, -1, -1):
            mask = ans | (1 << bit)

            aa = [x & mask for x in a]
            bb = [(x & mask) ^ mask for x in b]

            aa.sort()
            bb.sort()

            if aa == bb:
                ans = mask

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()