import sys
import bisect

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, m = data[0], data[1]
    a = data[2:2 + n]

    mid = n // 2
    left = a[:mid]
    right = a[mid:]

    def subset_sums(arr):
        sums = [0]
        for value in arr:
            value %= m
            sums += [(x + value) % m for x in sums]
        return sums

    left_sums = subset_sums(left)
    right_sums = subset_sums(right)

    left_sums.sort()

    ans = 0
    max_left = left_sums[-1]

    for s in right_sums:
        target = m - 1 - s
        idx = bisect.bisect_right(left_sums, target) - 1

        if idx >= 0:
            ans = max(ans, s + left_sums[idx])

        ans = max(ans, (s + max_left) % m)

        if ans == m - 1:
            break

    print(ans)

if __name__ == "__main__":
    main()