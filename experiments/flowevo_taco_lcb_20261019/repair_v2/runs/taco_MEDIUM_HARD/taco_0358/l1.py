import sys


def main() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    m = next(data)

    first = [next(data) for _ in range(n)]

    if n == 1:
        print(1)
        return

    good = bytearray([1]) * (n - 1)

    for _ in range(m - 1):
        pos = [0] * (n + 1)

        for i in range(1, n + 1):
            pos[next(data)] = i

        for i in range(n - 1):
            if good[i]:
                a = first[i]
                b = first[i + 1]
                if pos[a] + 1 != pos[b]:
                    good[i] = 0

    answer = n
    run = 0

    for value in good:
        if value:
            run += 1
            answer += run
        else:
            run = 0

    print(answer)


if __name__ == "__main__":
    main()