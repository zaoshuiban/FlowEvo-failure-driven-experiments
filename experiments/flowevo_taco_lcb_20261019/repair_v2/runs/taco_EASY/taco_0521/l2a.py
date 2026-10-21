import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    n = data[0]
    degrees = data[1:1 + n]

    if n == 1:
        is_tree = (len(degrees) == 1 and degrees[0] == 0)
    else:
        is_tree = (
            len(degrees) == n
            and all(d > 0 for d in degrees)
            and sum(degrees) == 2 * (n - 1)
        )

    print("Yes" if is_tree else "No")

if __name__ == "__main__":
    main()