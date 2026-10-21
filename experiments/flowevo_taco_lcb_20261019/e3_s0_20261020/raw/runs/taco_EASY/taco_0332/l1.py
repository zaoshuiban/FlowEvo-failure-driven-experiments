import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    ans = 0
    rem = 0  # garbage left from the previous day that must be disposed today

    for x in a:
        if rem > 0:
            need = k - rem
            use = min(x, need)
            x -= use
            ans += 1
            rem = 0

        ans += x // k
        rem = x % k

    if rem > 0:
        ans += 1

    print(ans)

if __name__ == "__main__":
    solve()