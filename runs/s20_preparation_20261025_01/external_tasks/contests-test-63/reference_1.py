import sys

inp = sys.stdin.readline

def solve():
    n = int(inp())
    a = [[0] for i in range(n)]
    mb = [0] * (1 << n)
    for i in range(n):
        s = inp().strip()
        m = 0
        b = 0
        for c in s:
            if c == '(':
                b += 1
            else:
                b -= 1
                if b <= 0:
                    if m > b:
                        m = b
                        a[i].append(1)
                    elif m == b:
                        a[i][-1] += 1
        mb[1 << i] = b
    dp = [None] * (1 << n)
    dp[0] = 0
    ans = 0
    for i in range(1, 1 << n):
        j = i & (i - 1)
        if j:
            mb[i] = mb[i-j] + mb[j]
        nd = None
        for j in range(n):
            if (i >> j) & 1:
                d = dp[i - (1 << j)]
                if d is not None:
                    bb = mb[i - (1 << j)]
                    m = len(a[j]) - 1
                    if bb - m < 0:
                        ans = max(ans, a[j][bb] + d)
                    elif bb - m == 0:
                        if nd is None:
                            nd = a[j][-1] + d
                        else:
                            nd = max(nd, a[j][-1] + d)
                    else:
                        if nd is None:
                            nd = d
                        else:
                            nd = max(nd, d)
        if nd is not None:
            ans = max(ans, nd)
        dp[i] = nd
    print(ans)

def main():
    solve()

if __name__ == '__main__':
    main()
