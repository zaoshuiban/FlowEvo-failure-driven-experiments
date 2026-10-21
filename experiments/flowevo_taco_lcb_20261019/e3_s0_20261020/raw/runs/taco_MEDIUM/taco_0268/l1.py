import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for x in data[1:1 + t]:
        possible = False

        for use_111 in range(11):
            remaining = x - 111 * use_111
            if remaining >= 0 and remaining % 11 == 0:
                possible = True
                break

        ans.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()