import sys
from array import array

def main():
    data = sys.stdin.buffer.read()
    length = len(data)
    idx = 0

    while idx < length and data[idx] <= 32:
        idx += 1

    n = 0
    while idx < length and data[idx] > 32:
        n = n * 10 + (data[idx] - 48)
        idx += 1

    values = array('I')
    xor_sum = 0

    for _ in range(n):
        while idx < length and data[idx] <= 32:
            idx += 1

        val = 0
        while idx < length and data[idx] > 32:
            val = val * 10 + (data[idx] - 48)
            idx += 1

        values.append(val)
        xor_sum ^= val

    if xor_sum == 0:
        sys.stdout.write("0\n")
        return

    highest_bit = 1 << (xor_sum.bit_length() - 1)

    answer = 0
    for val in values:
        if val & highest_bit:
            answer += 1

    sys.stdout.write(str(answer) + "\n")


if __name__ == "__main__":
    main()