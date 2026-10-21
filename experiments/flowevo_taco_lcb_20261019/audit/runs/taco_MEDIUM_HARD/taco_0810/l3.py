import sys
from array import array


def main():
    data = sys.stdin.buffer.read()
    length = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return num

    n = next_int()
    m = next_int()
    c = next_int()

    bit = array('q', [0]) * (n + 2)
    answers = []

    for _ in range(m):
        while idx < length and data[idx] <= 32:
            idx += 1

        op = data[idx]
        idx += 1

        if op == ord('S'):
            u = next_int()
            v = next_int()
            k = next_int()

            i = u
            while i <= n:
                bit[i] += k
                i += i & -i

            i = v + 1
            neg_k = -k
            while i <= n:
                bit[i] += neg_k
                i += i & -i

        else:
            p = next_int()

            total = 0
            i = p
            while i > 0:
                total += bit[i]
                i -= i & -i

            answers.append(str(c + total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()