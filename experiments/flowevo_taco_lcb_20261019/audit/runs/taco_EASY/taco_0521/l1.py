import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    n = data[0]
    degrees = data[1:1 + n]

    if sum(degrees) == 2 * (n - 1):
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    main()