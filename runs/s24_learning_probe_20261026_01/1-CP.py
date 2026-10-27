import sys

def solve():
    n, m, k, x, y = map(int, sys.stdin.readline().split())

    if n == 1:
        full = k // m
        rem = k % m
        max_q = full + (1 if rem > 0 else 0)
        min_q = full
        sergei = full + (1 if y <= rem else 0)
        print(max_q, min_q, sergei)
        return

    cycle_len = 2 * (n - 1) * m
    full_cycles = k // cycle_len
    rem = k % cycle_len

    base = [0] * (n + 1)
    for i in range(1, n + 1):
        if i == 1 or i == n:
            base[i] = full_cycles
        else:
            base[i] = 2 * full_cycles

    row = 1
    direction = 1
    for _ in range(rem):
        base[row] += 1
        if row == n:
            direction = -1
        elif row == 1:
            direction = 1
        row += direction

    max_q = max(base[1:])
    min_q = min(base[1:])
    sergei = base[x]

    print(max_q, min_q, sergei)

if __name__ == "__main__":
    solve()