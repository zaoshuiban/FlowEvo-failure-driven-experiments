import sys


def min_operations(a: int, b: int) -> int:
    best = 10**18
    inc = 0

    while True:
        new_b = b + inc

        if new_b > 1:
            divisions = 0
            x = a

            while x > 0:
                x //= new_b
                divisions += 1

            best = min(best, inc + divisions)

        inc += 1

        # Further increments alone already cost at least 'best',
        # so they cannot produce a better answer.
        if inc >= best:
            break

    return best


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    answer = []

    idx = 1
    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        answer.append(str(min_operations(a, b)))

    sys.stdout.write("\n".join(answer))


if __name__ == "__main__":
    main()