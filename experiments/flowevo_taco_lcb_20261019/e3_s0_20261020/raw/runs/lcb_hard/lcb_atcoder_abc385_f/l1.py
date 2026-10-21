import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    X = [0] * n
    H = [0] * n

    p = 1
    for i in range(n):
        X[i] = data[p]
        H[i] = data[p + 1]
        p += 2

    if n == 1:
        print(-1)
        return

    hull = []
    bp_num = []
    bp_den = []

    best_num = None
    best_den = 1

    for i in range(n):
        if not hull:
            hull.append(i)
            continue

        j = hull[-1]
        c_num = X[i] * H[j] - X[j] * H[i]
        c_den = X[i] - X[j]

        while len(hull) >= 2:
            if c_num * bp_den[-1] <= bp_num[-1] * c_den:
                hull.pop()
                bp_num.pop()
                bp_den.pop()

                j = hull[-1]
                c_num = X[i] * H[j] - X[j] * H[i]
                c_den = X[i] - X[j]
            else:
                break

        if best_num is None or c_num * best_den > best_num * c_den:
            best_num = c_num
            best_den = c_den

        hull.append(i)
        bp_num.append(c_num)
        bp_den.append(c_den)

    if best_num is None or best_num < 0:
        print(-1)
    else:
        ans = best_num / best_den
        if abs(ans) < 5e-20:
            ans = 0.0
        print(f"{ans:.20f}")


if __name__ == "__main__":
    solve()