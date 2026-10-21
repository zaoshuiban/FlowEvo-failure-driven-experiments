import sys
import math
import io


def read_numbers():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False
    for ch in data:
        if 48 <= ch <= 57:
            num = num * 10 + (ch - 48)
            inside = True
        elif inside:
            yield num
            num = 0
            inside = False
    if inside:
        yield num


def main():
    it = read_numbers()

    try:
        t = next(it)
    except StopIteration:
        return

    out = io.StringIO()

    for _ in range(t):
        n = next(it)
        e = next(it)
        o = next(it)

        total = n * (n + 1) // 2

        if e + o != total:
            out.write("-1\n")
            continue

        if n == 0:
            out.write("\n")
            continue

        if o == 0:
            out.write("2" + " 2" * (n - 1))
            out.write("\n")
            continue

        m = n + 1
        d = m * m - 4 * o

        if d < 0:
            out.write("-1\n")
            continue

        s = math.isqrt(d)

        if s * s != d:
            out.write("-1\n")
            continue

        # Choose the smaller position of the unique odd element.
        p = (m - s) // 2

        if not (1 <= p <= n) or p * (m - p) != o:
            p = (m + s) // 2
            if not (1 <= p <= n) or p * (m - p) != o:
                out.write("-1\n")
                continue

        q = m - p
        even_subarrays = p * (p - 1) // 2 + q * (q - 1) // 2

        if even_subarrays != e:
            out.write("-1\n")
            continue

        if p == 1:
            line = "1"
        else:
            line = "2 " * (p - 1) + "1"

        if n > p:
            line += " 2" * (n - p)

        out.write(line)
        out.write("\n")

    sys.stdout.write(out.getvalue())


if __name__ == "__main__":
    main()