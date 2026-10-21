import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        n = int(data[i])

        equal = (360 % n == 0)
        possible = (n <= 360)
        distinct = (n * (n + 1) // 2 <= 360)

        ans.append(
            ('y' if equal else 'n') + ' ' +
            ('y' if possible else 'n') + ' ' +
            ('y' if distinct else 'n')
        )

    sys.stdout.write('\n'.join(ans))

if __name__ == "__main__":
    solve()