import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    divisors = data[1:1 + n]

    x = max(divisors)

    count = {}
    for d in divisors:
        count[d] = count.get(d, 0) + 1

    for d in list(count.keys()):
        if x % d == 0:
            count[d] -= 1

    y = max(d for d, c in count.items() if c > 0)

    print(x, y)

if __name__ == "__main__":
    main()