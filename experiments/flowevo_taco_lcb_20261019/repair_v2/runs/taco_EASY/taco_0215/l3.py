import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, h = data[0], data[1]
    a = data[2:2 + n]

    def can(k):
        b = sorted(a[:k])
        total = 0
        for i in range(k - 1, -1, -2):
            total += b[i]
            if total > h:
                return False
        return True

    lo, hi = 0, n + 1

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if can(mid):
            lo = mid
        else:
            hi = mid

    print(lo)

if __name__ == "__main__":
    main()