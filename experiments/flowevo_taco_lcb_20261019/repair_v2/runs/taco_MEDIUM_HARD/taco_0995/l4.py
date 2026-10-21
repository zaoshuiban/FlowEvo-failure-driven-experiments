import sys


def main() -> None:
    data = sys.stdin.buffer.read()
    length = len(data)
    pos = 0

    def next_int() -> int:
        nonlocal pos
        while pos < length and data[pos] <= 32:
            pos += 1
        num = 0
        while pos < length and data[pos] > 32:
            num = num * 10 + (data[pos] - 48)
            pos += 1
        return num

    n = next_int()

    unusual = 0
    for i in range(n):
        for j in range(n):
            value = next_int()
            if i == j:
                unusual ^= value

    q = next_int()
    answers = bytearray()

    for _ in range(q):
        query_type = next_int()
        if query_type == 3:
            answers.append(48 + unusual)
        else:
            next_int()  # row/column index is irrelevant
            unusual ^= 1

    sys.stdout.buffer.write(answers)


if __name__ == "__main__":
    main()