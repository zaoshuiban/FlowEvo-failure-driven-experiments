import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    def can_make(k):
        for i in range(k):
            if 2 * a[i] > a[n - k + i]:
                return False
        return True

    low, high = 0, n // 2

    while low < high:
        mid = (low + high + 1) // 2
        if can_make(mid):
            low = mid
        else:
            high = mid - 1

    print(low)

if __name__ == "__main__":
    main()