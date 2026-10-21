import sys

def main():
    a, b = map(int, sys.stdin.readline().split())

    if a < b:
        print(-1)
        return

    candidates = []

    # Point lies on an ascending segment:
    # x = (a - b) / (2n), n >= 1, and x >= b
    if a > b:
        num = a - b
        n = num // (2 * b)
        if n >= 1:
            candidates.append((num, 2 * n))

    # Point lies on a descending segment:
    # x = (a + b) / (2n), n >= 1, and x >= b
    num = a + b
    n = num // (2 * b)
    candidates.append((num, 2 * n))

    best_num, best_den = candidates[0]

    for num, den in candidates[1:]:
        if num * best_den < best_num * den:
            best_num, best_den = num, den

    print(f"{best_num / best_den:.15f}")

if __name__ == "__main__":
    main()