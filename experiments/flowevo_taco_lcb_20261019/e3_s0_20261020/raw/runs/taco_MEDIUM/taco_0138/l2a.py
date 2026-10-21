import sys
from array import array


def ints_from_bytes(data):
    num = 0
    inside = False
    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            inside = True
        elif inside:
            yield num
            num = 0
            inside = False
    if inside:
        yield num


def main():
    data = sys.stdin.buffer.read()
    it = ints_from_bytes(data)

    try:
        n = next(it)
    except StopIteration:
        return

    piles = array('I')
    xor_sum = 0

    for _ in range(n):
        value = next(it)
        piles.append(value)
        xor_sum ^= value

    if xor_sum == 0:
        sys.stdout.write("0\n")
        return

    ans = 0
    for value in piles:
        if (value ^ xor_sum) < value:
            ans += 1

    sys.stdout.write(str(ans) + "\n")


if __name__ == "__main__":
    main()