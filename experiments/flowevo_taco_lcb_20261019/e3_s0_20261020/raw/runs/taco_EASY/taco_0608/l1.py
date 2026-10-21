import sys

def main():
    p, x, y = map(int, sys.stdin.readline().split())

    target = p - 26
    good = [False] * 475

    for start in range(475):
        i = start
        for _ in range(25):
            i = (i * 96 + 42) % 475
            if i == target:
                good[start] = True
                break

    q0 = x // 50
    r = x % 50
    qmin = (y - r + 49) // 50

    successful = 0
    while True:
        upper = q0 + 2 * successful

        if upper >= qmin:
            length = upper - qmin + 1
            limit = min(length, 475)

            for q in range(qmin, qmin + limit):
                if good[q % 475]:
                    print(successful)
                    return

        successful += 1


if __name__ == "__main__":
    main()