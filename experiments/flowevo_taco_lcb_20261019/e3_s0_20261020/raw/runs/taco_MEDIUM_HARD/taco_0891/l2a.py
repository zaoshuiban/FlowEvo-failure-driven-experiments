import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    s, x = map(int, data[:2])

    if s < x or (s - x) % 2 != 0:
        print(0)
        return

    common = (s - x) // 2

    if common & x:
        print(0)
        return

    ans = 1 << x.bit_count()

    # If common == 0, the cases where one of the numbers is zero are included.
    if common == 0:
        ans -= 2

    print(ans)

if __name__ == "__main__":
    main()