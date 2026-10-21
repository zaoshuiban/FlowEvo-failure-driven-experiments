import sys
import math
import io


def main():
    data = sys.stdin.buffer.read()

    def integers():
        num = 0
        inside = False
        for ch in data:
            if 48 <= ch <= 57:
                num = num * 10 + (ch - 48)
                inside = True
            else:
                if inside:
                    yield num
                    num = 0
                    inside = False
        if inside:
            yield num

    it = integers()
    t = next(it)
    output = io.StringIO()

    for _ in range(t):
        n = next(it)
        e = next(it)
        o = next(it)

        total = n * (n + 1) // 2

        if e + o != total:
            output.write("-1\n")
            continue

        m = n + 1
        d = m * m - 4 * o

        if d < 0:
            output.write("-1\n")
            continue

        s = math.isqrt(d)

        if s * s != d:
            output.write("-1\n")
            continue

        c = (m + s) // 2

        if c < 1 or c > m or c * (m - c) != o:
            c = (m - s) // 2
            if c < 1 or c > m or c * (m - c) != o:
                output.write("-1\n")
                continue

        arr = ['2'] * n

        if c <= n:
            arr[c - 1] = '1'

        output.write(' '.join(arr))
        output.write('\n')

    sys.stdout.write(output.getvalue())


if __name__ == "__main__":
    main()