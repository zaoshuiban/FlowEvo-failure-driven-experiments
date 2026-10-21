import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        l = data[idx + 2]
        idx += 3

        speeds = data[idx:idx + n]
        idx += n

        friend = speeds[-1]

        if n == 1:
            ans.append("Yes")
            continue

        max_other = max(speeds[:-1])

        if k > 0:
            best_speed = friend + (l - 1) * k
        else:
            best_speed = friend

        ans.append("Yes" if best_speed > max_other else "No")

    print("\n".join(ans))

if __name__ == "__main__":
    solve()