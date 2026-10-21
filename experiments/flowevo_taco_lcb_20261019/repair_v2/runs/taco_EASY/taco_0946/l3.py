import sys

def main():
    l, r = map(int, sys.stdin.buffer.readline().split())

    if r - l >= 2 and l % 2 == 0:
        print(l, l + 1, l + 2)
    elif r - l >= 3 and l % 2 == 1:
        print(l + 1, l + 2, l + 3)
    else:
        print(-1)

if __name__ == "__main__":
    main()