import sys

def solve() -> None:
    data = sys.stdin.buffer
    n, t = map(int, data.readline().split())
    s = data.readline().strip()

    total_houses = s.count(b'H')
    total_shops = s.count(b'S')
    rightmost_house = s.rfind(b'H') + 1  # 1-indexed position

    # Even with all needed candies, we must reach the rightmost house.
    if t < rightmost_house:
        print(-1)
        return

    H = total_houses
    S_total = total_shops
    R = rightmost_house

    def feasible(k: int) -> bool:
        if k + S_total < H:
            return False

        balance = k
        deficit_count = 0
        best_f = 0
        shops = 0

        for idx, ch in enumerate(s, 1):
            # Prefix of length idx-1 is before the edge (idx-1, idx).
            if balance < 0:
                deficit_count += 1

            f = -idx + 2 * deficit_count
            if f < best_f:
                best_f = f

            if ch == 72:       # 'H'
                balance -= 1
            elif ch == 83:     # 'S'
                balance += 1
                shops += 1

            if idx >= R and k + shops >= H:
                minimum_time = 2 * idx + best_f
                return minimum_time <= t

        return False

    lo = -1
    hi = H

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid

    print(hi)


if __name__ == "__main__":
    solve()