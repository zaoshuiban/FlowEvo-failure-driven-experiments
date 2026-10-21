import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    ans = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        total_xor = 0
        for x in a:
            total_xor ^= x

        if total_xor == 0:
            ans.append("DRAW")
            continue

        highest_bit = 1 << (total_xor.bit_length() - 1)
        cnt = sum(1 for x in a if x & highest_bit)

        if cnt % 4 == 1:
            ans.append("WIN")
        else:
            if (n - cnt) % 2 == 1:
                ans.append("WIN")
            else:
                ans.append("LOSE")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()