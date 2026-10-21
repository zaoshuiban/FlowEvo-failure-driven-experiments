import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        if (n == 1 and m == 2) or (n == 2 and m == 1):
            ans.append("Yes")
        elif n > 1 and m > 1 and (n % 2 == 0 or m % 2 == 0):
            ans.append("Yes")
        else:
            ans.append("No")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()