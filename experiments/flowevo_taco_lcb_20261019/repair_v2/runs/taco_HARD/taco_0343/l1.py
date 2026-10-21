import sys
import heapq


def main():
    data = sys.stdin.buffer.read()
    pos = 0
    length = len(data)

    def next_int():
        nonlocal pos
        while pos < length and data[pos] <= 32:
            pos += 1
        num = 0
        while pos < length and data[pos] > 32:
            num = num * 10 + (data[pos] - 48)
            pos += 1
        return num

    n = next_int()

    c = [0] * n
    a = [None] * n
    mult = [1] * n

    prod = 1
    for i in range(n):
        ci = next_int()
        c[i] = ci

        arr = [0] * ci
        for j in range(ci):
            arr[j] = next_int()
        a[i] = arr

        mult[i] = prod
        prod *= ci

    m = next_int()
    banned = set()

    for _ in range(m):
        code = 0
        for i in range(n):
            code += (next_int() - 1) * mult[i]
        banned.add(code)

    start_code = 0
    for i in range(n):
        start_code += (c[i] - 1) * mult[i]

    if start_code not in banned:
        sys.stdout.write(" ".join(map(str, c)) + "\n")
        return

    bits = (prod - 1).bit_length()
    mask = (1 << bits) - 1 if bits else 0

    heap = [start_code]
    heappop = heapq.heappop
    heappush = heapq.heappush

    while heap:
        entry = heappop(heap)

        key = entry >> bits
        code = entry & mask

        if code not in banned:
            temp = code
            answer = []

            for i in range(n):
                answer.append(str(temp % c[i] + 1))
                temp //= c[i]

            sys.stdout.write(" ".join(answer) + "\n")
            return

        temp = code

        for i in range(n):
            ci = c[i]
            digit = temp % ci
            temp //= ci

            if digit > 0:
                ncode = code - mult[i]
                diff = a[i][digit] - a[i][digit - 1]
                nkey = key + diff
                heappush(heap, (nkey << bits) + ncode)

            if digit != ci - 1:
                break


if __name__ == "__main__":
    main()