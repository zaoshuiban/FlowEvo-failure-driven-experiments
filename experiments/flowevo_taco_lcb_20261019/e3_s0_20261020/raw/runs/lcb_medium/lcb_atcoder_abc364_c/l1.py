import sys

def main():
    input = sys.stdin.buffer.readline

    N, X, Y = map(int, input().split())
    A = list(map(int, input().split()))
    B = list(map(int, input().split()))

    A.sort(reverse=True)
    B.sort(reverse=True)

    ans = N

    sum_a = 0
    for i in range(N):
        sum_a += A[i]
        if sum_a > X:
            ans = min(ans, i + 1)
            break

    sum_b = 0
    for i in range(N):
        sum_b += B[i]
        if sum_b > Y:
            ans = min(ans, i + 1)
            break

    print(ans)


if __name__ == "__main__":
    main()