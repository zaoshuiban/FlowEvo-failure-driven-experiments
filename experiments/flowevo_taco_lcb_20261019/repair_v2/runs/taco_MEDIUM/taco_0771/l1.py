import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for n in data[1:t + 1]:
        low = 1
        high = n
        perm = []

        for i in range(n):
            if i % 2 == 0:
                perm.append(str(high))
                high -= 1
            else:
                perm.append(str(low))
                low += 1

        ans.append(" ".join(perm))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()