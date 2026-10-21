import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    if k == 1:
        targets = [1]
    elif k == -1:
        targets = [1, -1]
    else:
        targets = []
        power = 1
        LIMIT = 10**18

        while abs(power) <= LIMIT:
            targets.append(power)
            power *= k

    freq = {0: 1}
    prefix_sum = 0
    answer = 0

    for value in a:
        prefix_sum += value

        for target in targets:
            answer += freq.get(prefix_sum - target, 0)

        freq[prefix_sum] = freq.get(prefix_sum, 0) + 1

    print(answer)


if __name__ == "__main__":
    main()