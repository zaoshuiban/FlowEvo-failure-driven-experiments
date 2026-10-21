import sys

def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)
    ans = []

    for _ in range(t):
        n = next(data)

        both = 0       # needed by both players
        first_only = 0 # needed only by First
        second_only = 0# needed only by Second

        for i in range(1, n + 1):
            p = next(data)

            good_asc = (p == i)
            good_desc = (p == n + 1 - i)

            if not good_asc and not good_desc:
                both += 1
            elif not good_asc:
                first_only += 1
            elif not good_desc:
                second_only += 1

        if both + first_only <= second_only:
            ans.append("First")
        elif both + second_only < first_only:
            ans.append("Second")
        else:
            ans.append("Tie")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()