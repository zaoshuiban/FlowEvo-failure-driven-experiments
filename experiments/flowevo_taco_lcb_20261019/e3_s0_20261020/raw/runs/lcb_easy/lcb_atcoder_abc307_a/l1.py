import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = data[1:]

    ans = [sum(A[i * 7:(i + 1) * 7]) for i in range(N)]
    print(*ans)

if __name__ == "__main__":
    main()