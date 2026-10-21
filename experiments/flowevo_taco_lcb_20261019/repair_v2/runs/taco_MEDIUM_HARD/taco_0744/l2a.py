import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    limit = sum(abs(x) for x in a)

    powers = set()

    if k == 1:
        powers.add(1)
    elif k == -1:
        powers.add(1)
        powers.add(-1)
    else:
        power = 1
        while abs(power) <= limit:
            powers.add(power)
            power *= k

    powers = tuple(powers)

    prefix_count = {0: 1}
    current_sum = 0
    answer = 0

    for value in a:
        current_sum += value

        for power in powers:
            answer += prefix_count.get(current_sum - power, 0)

        prefix_count[current_sum] = prefix_count.get(current_sum, 0) + 1

    print(answer)


if __name__ == "__main__":
    main()