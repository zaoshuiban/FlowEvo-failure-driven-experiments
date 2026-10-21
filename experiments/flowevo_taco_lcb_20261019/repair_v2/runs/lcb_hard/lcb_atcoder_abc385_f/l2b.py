import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    if n == 1:
        print(-1)
        return

    x1, h1 = data[1], data[2]

    best_num = None
    best_den = 1

    idx = 3
    for _ in range(n - 1):
        x2, h2 = data[idx], data[idx + 1]
        idx += 2

        # Need h > (h1 * x2 - h2 * x1) / (x2 - x1)
        num = h1 * x2 - h2 * x1
        den = x2 - x1

        if best_num is None or num * best_den > best_num * den:
            best_num = num
            best_den = den

        x1, h1 = x2, h2

    if best_num is None or best_num < 0:
        print(-1)
    else:
        integer_part = best_num // best_den
        remainder = best_num % best_den

        digits = 18
        fractional_part = (remainder * (10 ** digits)) // best_den

        print(f"{integer_part}.{fractional_part:0{digits}d}")

if __name__ == "__main__":
    main()