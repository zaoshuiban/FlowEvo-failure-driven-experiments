import sys

def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    ans = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        mn = [0] * m
        mx = [0] * m

        for i in range(n):
            for j in range(m):
                v = next(it)

                if i == 0 and j == 0:
                    mn[j] = mx[j] = v
                else:
                    if i == 0:
                        best_min = mn[j - 1]
                        best_max = mx[j - 1]
                    elif j == 0:
                        best_min = mn[j]
                        best_max = mx[j]
                    else:
                        best_min = min(mn[j], mn[j - 1])
                        best_max = max(mx[j], mx[j - 1])

                    mn[j] = best_min + v
                    mx[j] = best_max + v

        path_length = n + m - 1

        if path_length % 2 == 0 and mn[m - 1] <= 0 <= mx[m - 1]:
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()