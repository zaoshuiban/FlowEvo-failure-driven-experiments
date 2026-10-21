import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        if k not in a:
            ans.append("no")
            continue

        if n == 1:
            ans.append("yes")
            continue

        possible = False

        # We need two elements >= k at distance at most 2.
        for i in range(n):
            if a[i] >= k:
                if i >= 1 and a[i - 1] >= k:
                    possible = True
                    break
                if i >= 2 and a[i - 2] >= k:
                    possible = True
                    break

        ans.append("yes" if possible else "no")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()