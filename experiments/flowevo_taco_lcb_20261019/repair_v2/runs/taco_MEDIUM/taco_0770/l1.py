import sys
from array import array


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    sign = 1
    in_num = False

    for c in data:
        if c == 45:  # '-'
            sign = -1
        elif 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        else:
            if in_num:
                yield sign * num
                num = 0
                sign = 1
                in_num = False
            else:
                sign = 1

    if in_num:
        yield sign * num


def main():
    it = read_ints()

    try:
        n = next(it)
    except StopIteration:
        return

    arr = array('q', [0]) * n

    total = 0
    pmean = 0

    for i in range(n):
        x = next(it)
        arr[i] = x
        total += x
        pmean += (i + 1) * x

    ans = pmean

    for i in range(n - 1):
        pmean = pmean - total + n * arr[i]
        if pmean > ans:
            ans = pmean

    sys.stdout.write(str(ans))


if __name__ == "__main__":
    main()