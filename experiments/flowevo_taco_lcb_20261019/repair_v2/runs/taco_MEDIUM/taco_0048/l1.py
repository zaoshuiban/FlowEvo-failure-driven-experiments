import sys

def main():
    n = int(sys.stdin.readline().strip())
    m = n

    rad = 1
    exponents = []

    if m % 2 == 0:
        rad *= 2
        cnt = 0
        while m % 2 == 0:
            m //= 2
            cnt += 1
        exponents.append(cnt)

    p = 3
    while p * p <= m:
        if m % p == 0:
            rad *= p
            cnt = 0
            while m % p == 0:
                m //= p
                cnt += 1
            exponents.append(cnt)
        p += 2

    if m > 1:
        rad *= m
        exponents.append(1)

    if not exponents:
        print(1, 0)
        return

    mx = max(exponents)

    steps = 0
    target = 1
    while target < mx:
        target <<= 1
        steps += 1

    need_mul = any(cnt != target for cnt in exponents)
    operations = steps + (1 if need_mul else 0)

    print(rad, operations)


if __name__ == "__main__":
    main()