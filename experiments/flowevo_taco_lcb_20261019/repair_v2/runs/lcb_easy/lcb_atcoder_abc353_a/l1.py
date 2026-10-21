import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    N = data[0]
    H = data[1:1 + N]

    first_height = H[0]

    for i in range(1, N):
        if H[i] > first_height:
            print(i + 1)
            return

    print(-1)

if __name__ == "__main__":
    main()