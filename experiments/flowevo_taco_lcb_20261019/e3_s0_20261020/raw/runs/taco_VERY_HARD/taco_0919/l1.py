import sys
import io
from math import isqrt


def ints_from_bytes(data):
    i = 0
    n = len(data)
    while i < n:
        while i < n and data[i] <= 32:
            i += 1
        if i >= n:
            break
        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1
        yield num


def main():
    data = sys.stdin.buffer.read()
    it = ints_from_bytes(data)

    try:
        T = next(it)
    except StopIteration:
        return

    out = io.StringIO()

    for _ in range(T):
        n = next(it)
        E = next(it)
        O = next(it)

        total = n * (n + 1) // 2

        if E + O != total:
            out.write("-1\n")
            continue

        if n == 0:
            if E == 0 and O == 0:
                out.write("\n")
            else:
                out.write("-1\n")
            continue

        m = n + 1
        D = m * m - 4 * O

        if D < 0:
            out.write("-1\n")
            continue

        root = isqrt(D)

        if root * root != D:
            out.write("-1\n")
            continue

        k = (m - root) // 2

        if not (0 <= k <= n and k * (m - k) == O):
            k2 = (m + root) // 2
            if 0 <= k2 <= n and k2 * (m - k2) == O:
                k = k2
            else:
                out.write("-1\n")
                continue

        arr = ['2'] * n

        if k > 0:
            arr[0] = '1'
            if k < n:
                arr[k] = '1'

        out.write(' '.join(arr))
        out.write('\n')

    sys.stdout.write(out.getvalue())


if __name__ == "__main__":
    main()