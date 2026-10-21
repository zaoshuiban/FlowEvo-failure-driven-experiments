import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n, k, l = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        speeds = data[idx:idx + n]
        idx += n

        friend_speed = speeds[-1]

        if n == 1:
            ans.append("Yes")
            continue

        max_other = max(speeds[:-1])

        if k > 0:
            best_speed = friend_speed + k * (l - 1)
        else:
            best_speed = friend_speed

        if best_speed > max_other:
            ans.append("Yes")
        else:
            ans.append("No")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()