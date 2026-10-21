import sys

def solve() -> None:
    input = sys.stdin.readline
    n, h = map(int, input().split())
    a = list(map(int, input().split()))

    def can(k: int) -> bool:
        bottles = sorted(a[:k], reverse=True)
        total = 0
        for i in range(0, k, 2):
            total += bottles[i]
            if total > h:
                return False
        return True

    left, right = 1, n
    answer = 1

    while left <= right:
        mid = (left + right) // 2
        if can(mid):
            answer = mid
            left = mid + 1
        else:
            right = mid - 1

    print(answer)

if __name__ == "__main__":
    solve()