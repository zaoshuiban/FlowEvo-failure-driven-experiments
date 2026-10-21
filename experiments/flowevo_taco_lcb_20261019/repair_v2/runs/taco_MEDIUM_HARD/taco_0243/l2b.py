import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    a = int(data[0])
    b = int(data[1])

    if a < b:
        print(-1)
        return

    # Candidate from falling segments:
    # x = (a + b) / (2 * m), maximize valid m.
    num_fall = a + b
    m = num_fall // (2 * b)
    best_num = num_fall
    best_den = 2 * m

    # Candidate from rising segments:
    # x = (a - b) / (2 * k), maximize valid k.
    if a > b:
        num_rise = a - b
        k = num_rise // (2 * b)
        if k > 0:
            den_rise = 2 * k
            # Compare num_rise / den_rise < best_num / best_den
            if num_rise * best_den < best_num * den_rise:
                best_num = num_rise
                best_den = den_rise

    ans = best_num / best_den
    print(f"{ans:.15f}")

if __name__ == "__main__":
    main()