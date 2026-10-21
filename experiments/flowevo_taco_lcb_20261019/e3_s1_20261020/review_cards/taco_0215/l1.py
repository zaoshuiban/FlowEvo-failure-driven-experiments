import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, h = data[0], data[1]
    a = data[2:2 + n]

    def can(k: int) -> bool:
        b = sorted(a[:k], reverse=True)
        total_height = sum(b[i] for i in range(0, k, 2))
        return total_height <= h

    left, right = 0, n
    while left < right:
        mid = (left + right + 1) // 2
        if can(mid):
            left = mid
        else:
            right = mid - 1

    print(left)

if __name__ == "__main__":
    main()