import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    if n == 1:
        print(-1)
        return

    xs = data[1::2]
    hs = data[2::2]

    best_num = None
    best_den = 1

    for i in range(n - 1):
        num = hs[i] * xs[i + 1] - hs[i + 1] * xs[i]
        den = xs[i + 1] - xs[i]

        if best_num is None or num * best_den > best_num * den:
            best_num = num
            best_den = den

    if best_num < 0:
        print(-1)
    else:
        ans = best_num / best_den
        print(f"{ans:.18f}")


if __name__ == "__main__":
    main()