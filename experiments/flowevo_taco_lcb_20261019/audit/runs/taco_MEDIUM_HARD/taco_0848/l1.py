import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    ans = []

    for _ in range(t):
        n = next(it)
        only_first = 0
        only_second = 0
        both = 0

        for i in range(1, n + 1):
            v = next(it)
            ok_asc = (v == i)
            ok_desc = (v == n - i + 1)

            if not ok_asc and not ok_desc:
                both += 1
            elif not ok_asc and ok_desc:
                only_first += 1
            elif ok_asc and not ok_desc:
                only_second += 1

        if only_first + both <= only_second:
            ans.append("First")
        elif only_second + both < only_first:
            ans.append("Second")
        else:
            ans.append("Tie")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()