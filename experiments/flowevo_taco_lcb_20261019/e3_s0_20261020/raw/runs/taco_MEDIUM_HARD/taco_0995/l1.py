import sys

data = sys.stdin.buffer.read()
idx = 0
length = len(data)


def next_int():
    global idx
    while idx < length and data[idx] <= 32:
        idx += 1

    value = 0
    while idx < length and data[idx] > 32:
        value = value * 10 + (data[idx] - 48)
        idx += 1

    return value


def main():
    n = next_int()

    answer = 0
    for i in range(n):
        for j in range(n):
            value = next_int()
            if i == j:
                answer ^= value

    q = next_int()
    result = []

    for _ in range(q):
        query_type = next_int()

        if query_type == 3:
            result.append('1' if answer else '0')
        else:
            next_int()  # row/column index is not needed
            answer ^= 1

    sys.stdout.write(''.join(result))


if __name__ == "__main__":
    main()