import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = data[1:1 + N]

    ans = 0
    j = 0

    for x in A:
        target = 2 * x
        while j < N and A[j] < target:
            j += 1
        ans += N - j

    print(ans)

if __name__ == "__main__":
    main()