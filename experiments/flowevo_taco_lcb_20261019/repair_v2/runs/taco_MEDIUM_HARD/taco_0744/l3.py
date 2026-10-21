import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    k = data[1]
    a = data[2:2 + n]

    total_abs = 0
    for x in a:
        if x >= 0:
            total_abs += x
        else:
            total_abs -= x

    # All elements are zero, so every segment sum is 0,
    # which is not a non-negative integer power of k (|k| >= 1).
    if total_abs == 0:
        print(0)
        return

    if k == 1:
        targets = (1,)
    elif k == -1:
        targets = (1, -1)
    else:
        targets_list = []
        value = 1
        if k > 1:
            while value <= total_abs:
                targets_list.append(value)
                value *= k
        else:  # k < -1
            while abs(value) <= total_abs:
                targets_list.append(value)
                value *= k
        targets = tuple(targets_list)

    freq = {0: 1}
    prefix = 0
    answer = 0
    get = freq.get

    for x in a:
        prefix += x

        for power in targets:
            answer += get(prefix - power, 0)

        freq[prefix] = get(prefix, 0) + 1

    print(answer)


if __name__ == "__main__":
    main()