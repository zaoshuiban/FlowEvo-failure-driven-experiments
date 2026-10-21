import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, h = data[0], data[1]
    a = data[2:2 + n]

    def can(k):
        b = sorted(a[:k], reverse=True)
        total = 0
        for i in range(0, k, 2):
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