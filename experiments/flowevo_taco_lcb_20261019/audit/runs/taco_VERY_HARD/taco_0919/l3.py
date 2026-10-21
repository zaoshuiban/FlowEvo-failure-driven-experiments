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

        m = n + 1
        d = m * m - 4 * o

        if d < 0:
            out.write("-1\n")
            continue

        s = math.isqrt(d)

        if s * s != d:
            out.write("-1\n")
            continue

        # z = number of even prefix sums among P[0], P[1], ..., P[n]
        # Then number of odd prefix sums is m - z, and o = z * (m - z).
        z = None

        cand = (m + s) // 2
        if 1 <= cand <= m and cand * (m - cand) == o:
            z = cand
        else:
            cand = (m - s) // 2
            if 1 <= cand <= m and cand * (m - cand) == o:
                z = cand

        if z is None:
            out.write("-1\n")
            continue

        odd_prefixes = m - z

        # Verify the number of even-sum subarrays as well.
        even_count = (
            z * (z - 1) // 2
            + odd_prefixes * (odd_prefixes - 1) // 2
        )

        if even_count != e:
            out.write("-1\n")
            continue

        # Construct an array with one odd element at position z,
        # or all even elements when z = n + 1.
        if z <= n:
            left = z - 1
            right = n - z

            if left:
                line = "2 " * left + "1"
            else:
                line = "1"

            if right:
                line += " 2" * right

            out.write(line)
            out.write("\n")
        else:
            if n > 0:
                out.write("2" + " 2" * (n - 1))
            out.write("\n")

    sys.stdout.write(out.getvalue())


if __name__ == "__main__":
    main()