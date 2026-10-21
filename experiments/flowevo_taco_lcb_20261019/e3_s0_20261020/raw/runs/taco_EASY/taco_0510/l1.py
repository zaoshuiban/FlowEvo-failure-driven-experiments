import sys

def main():
    a = int(sys.stdin.readline().strip())

    if a % 2 == 1:
        b = (a * a - 1) // 2
        c = (a * a + 1) // 2
    else:
        m = a // 2
        b = m * m - 1
        c = m * m + 1

    print(a, b, c)

if __name__ == "__main__":
    main()