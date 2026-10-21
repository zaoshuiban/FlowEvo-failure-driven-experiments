import sys
import math

def main():
    R = int(sys.stdin.readline())
    M = 4 * R * R
    ans = 0

    for x in range(R):
        side = 2 * x + 1
        rem = M - side * side

        k = math.isqrt(rem)
        y_max = (k - 1) // 2
        f = y_max + 1  # number of valid y >= 0 for this x

        if x == 0:
            ans += 2 * f - 1
        else:
            ans += 4 * f - 2

    print(ans)

if __name__ == "__main__":
    main()