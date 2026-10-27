import sys
from collections import deque

def solve():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    V = list(map(int, data[1:n+1]))
    T = list(map(int, data[n+1:n+1+n]))

    pref = [0] * (n + 1)
    for i in range(n):
        pref[i+1] = pref[i] + T[i]

    ans = [0] * n
    q = deque()  # (start_day, volume)

    for i in range(n):
        q.append((i, V[i]))
        melted_today = 0

        while q:
            start, vol = q[0]
            total_melt = pref[i+1] - pref[start]
            if total_melt >= vol:
                melt_before_today = pref[i] - pref[start]
                remaining_before_today = vol - melt_before_today
                if remaining_before_today > 0:
                    melted_today += remaining_before_today
                q.popleft()
            else:
                break

        melted_today += len(q) * T[i]
        ans[i] = melted_today

    sys.stdout.write(' '.join(map(str, ans)))

if __name__ == "__main__":
    solve()