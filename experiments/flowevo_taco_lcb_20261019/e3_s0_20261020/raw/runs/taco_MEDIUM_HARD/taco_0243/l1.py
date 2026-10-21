import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    a, b = map(int, data[:2])

    if a < b:
        print(-1)
        return

    q = a // b + 1
    if q % 2 == 1:
        q -= 1

    ans = (a + b) / q
    print(f"{ans:.15f}")

if __name__ == "__main__":
    main()