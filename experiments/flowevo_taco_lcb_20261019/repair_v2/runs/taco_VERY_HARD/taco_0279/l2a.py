import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        xor_sum = 0

        for i in range(1, n + 1):
            a = data[idx]
            idx += 1

            if i % 2 == 1:
                # Odd-indexed pile: Grundy = a % 2
                xor_sum ^= (a & 1)
            else:
                # Even-indexed pile: Grundy = floor(a / 2)
                xor_sum ^= (a >> 1)

        if xor_sum != 0:
            ans.append("CHEF")
        else:
            ans.append("CHEFINA")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()