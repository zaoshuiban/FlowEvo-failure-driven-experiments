import sys


def main():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

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

    c = [0] * n
    a = [None] * n

    for i in range(n):
        ci = next_int()
        c[i] = ci
        arr = [0] * ci
        for j in range(ci):
            arr[j] = next_int()
        a[i] = arr

    mult = [1] * n
    for i in range(1, n):
        mult[i] = mult[i - 1] * c[i - 1]

    start_code = 0
    for i in range(n):
        start_code += (c[i] - 1) * mult[i]

    m = next_int()
    banned = set()

    for _ in range(m):
        code = 0
        for i in range(n):
            v = next_int() - 1
            code += v * mult[i]
        banned.add(code)

    if start_code not in banned:
        ans = [str(c[i]) for i in range(n)]
        sys.stdout.write(" ".join(ans))
        return

    best_sum = -1
    best_code = -1

    for code in banned:
        tmp = code
        digits = [0] * n
        banned_sum = 0

        for i in range(n):
            ci = c[i]
            d = tmp % ci
            tmp //= ci
            digits[i] = d
            banned_sum += a[i][d]

        for i in range(n):
            d = digits[i]
            if d > 0:
                new_code = code - mult[i]
                if new_code not in banned:
                    new_sum = banned_sum - a[i][d] + a[i][d - 1]
                    if new_sum > best_sum:
                        best_sum = new_sum
                        best_code = new_code

    tmp = best_code
    ans = []

    for i in range(n):
        ci = c[i]
        d = tmp % ci
        tmp //= ci
        ans.append(str(d + 1))

    sys.stdout.write(" ".join(ans))


if __name__ == "__main__":
    main()