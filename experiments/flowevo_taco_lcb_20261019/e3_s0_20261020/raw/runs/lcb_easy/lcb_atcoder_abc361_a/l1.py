import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    N, K, X = data[0], data[1], data[2]
    A = data[3:3 + N]

    B = A[:K] + [X] + A[K:]
    print(*B)

if __name__ == "__main__":
    main()