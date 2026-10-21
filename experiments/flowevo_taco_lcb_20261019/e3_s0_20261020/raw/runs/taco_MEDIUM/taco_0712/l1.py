import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        x = data[idx + 1]
        idx += 2

        total = x * pow(2, n - 1, MOD) % MOD
        ans.append(str(total))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()