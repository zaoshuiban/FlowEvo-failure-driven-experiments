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

            if i & 1:
                grundy = a & 1
            else:
                grundy = a >> 1

            xor_sum ^= grundy

        if xor_sum:
            ans.append("CHEF")
        else:
            ans.append("CHEFINA")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()