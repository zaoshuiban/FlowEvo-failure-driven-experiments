import sys

def main():
    N, M, P = map(int, sys.stdin.readline().split())
    if M > N:
        print(0)
    else:
        print((N - M) // P + 1)

if __name__ == "__main__":
    main()