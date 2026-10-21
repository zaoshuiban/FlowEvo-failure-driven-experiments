import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, W, L = data[0], data[1], data[2]
    trees = []

    idx = 3
    for _ in range(n):
        h, r = data[idx], data[idx + 1]
        trees.append((h, r))
        idx += 2

    def can(months):
        total = 0
        for h, r in trees:
            height = h + r * months
            if height >= L:
                total += height
                if total >= W:
                    return True
        return total >= W

    low = 0
    high = 1

    while not can(high):
        high *= 2

    while low < high:
        mid = (low + high) // 2
        if can(mid):
            high = mid
        else:
            low = mid + 1

    print(low)

if __name__ == "__main__":
    solve()