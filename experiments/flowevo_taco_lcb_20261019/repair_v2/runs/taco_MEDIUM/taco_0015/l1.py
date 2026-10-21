import sys

def main():
    a, x, y = map(int, sys.stdin.readline().split())

    if y % a == 0:
        print(-1)
        return

    row = y // a

    if row == 0:
        if -a < 2 * x < a:
            print(1)
        else:
            print(-1)
    elif row % 2 == 1:
        if -a < 2 * x < a:
            print((row // 2) * 3 + 2)
        else:
            print(-1)
    else:
        if -a < x < 0:
            print((row // 2) * 3)
        elif 0 < x < a:
            print((row // 2) * 3 + 1)
        else:
            print(-1)

if __name__ == "__main__":
    main()