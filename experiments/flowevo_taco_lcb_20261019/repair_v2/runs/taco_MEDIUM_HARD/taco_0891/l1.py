import sys

def main():
    s, x = map(int, sys.stdin.readline().split())

    if s < x or (s - x) % 2 != 0:
        print(0)
        return

    c = (s - x) // 2

    if c & x:
        print(0)
        return

    ans = 1 << x.bit_count()

    if c == 0:
        ans -= 2

    print(max(ans, 0))

if __name__ == "__main__":
    main()