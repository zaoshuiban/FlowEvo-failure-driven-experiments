import sys

def can(mask, a, b):
    count = {}
    for x in b:
        y = x & mask
        count[y] = count.get(y, 0) + 1

    for x in a:
        need = mask ^ (x & mask)
        c = count.get(need, 0)
        if c == 0:
            return False
        count[need] = c - 1

    return True


def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]
        b = [next(it) for _ in range(n)]

        ans = 0

        for bit in range(29, -1, -1):
            candidate = ans | (1 << bit)
            if can(candidate, a, b):
                ans = candidate

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()