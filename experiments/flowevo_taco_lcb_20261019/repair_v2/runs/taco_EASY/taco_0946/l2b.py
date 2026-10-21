import sys
import math

def main():
    l, r = map(int, sys.stdin.readline().split())

    for a in range(l, r + 1):
        for b in range(a + 1, r + 1):
            if math.gcd(a, b) != 1:
                continue
            for c in range(b + 1, r + 1):
                if math.gcd(b, c) == 1 and math.gcd(a, c) != 1:
                    print(a, b, c)
                    return

    print(-1)

if __name__ == "__main__":
    main()