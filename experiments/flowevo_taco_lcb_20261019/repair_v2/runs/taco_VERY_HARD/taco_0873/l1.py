import sys
from array import array


def ints():
    data = sys.stdin.buffer.read()
    i = 0
    n = len(data)
    while i < n:
        while i < n and data[i] <= 32:
            i += 1
        if i >= n:
            break

        sign = 1
        if data[i] == 45:  # '-'
            sign = -1
            i += 1

        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1

        yield sign * num


def main():
    it = ints()
    n = next(it)
    m = next(it)
    k = next(it)

    MOD = 998244353

    max_nm = max(n, m)
    pow2 = array('I', [1]) * (max_nm + 1)
    for i in range(1, max_nm + 1):
        pow2[i] = (pow2[i - 1] * 2) % MOD

    SHIFT = 20
    MASK = (1 << SHIFT) - 1

    current = {}

    # column -> packed (count_req_0, count_req_1)
    col = {}
    ccols = 0
    badcols = 0

    # row -> packed (count_req_0, count_req_1)
    rowcnt = {}
    crows = 0
    badrows = 0

    base0 = 0
    base1 = 0

    def add_col(y, r):
        nonlocal ccols, badcols
        p = col.get(y, 0)
        if p == 0:
            ccols += 1
            col[y] = (1 << SHIFT) if r == 0 else 1
        else:
            c0 = p >> SHIFT
            c1 = p & MASK
            was_bad = 1 if (c0 > 0 and c1 > 0) else 0

            if r == 0:
                c0 += 1
            else:
                c1 += 1

            now_bad = 1 if (c0 > 0 and c1 > 0) else 0
            if now_bad != was_bad:
                badcols += now_bad - was_bad

            col[y] = (c0 << SHIFT) | c1

    def remove_col(y, r):
        nonlocal ccols, badcols
        p = col[y]
        c0 = p >> SHIFT
        c1 = p & MASK
        was_bad = 1 if (c0 > 0 and c1 > 0) else 0

        if r == 0:
            c0 -= 1
        else:
            c1 -= 1

        now_bad = 1 if (c0 > 0 and c1 > 0) else 0
        if now_bad != was_bad:
            badcols += now_bad - was_bad

        if c0 + c1 == 0:
            del col[y]
            ccols -= 1
        else:
            col[y] = (c0 << SHIFT) | c1

    def add_row(x, r):
        nonlocal crows, badrows
        p = rowcnt.get(x, 0)
        if p == 0:
            crows += 1
            rowcnt[x] = (1 << SHIFT) if r == 0 else 1
        else:
            c0 = p >> SHIFT
            c1 = p & MASK
            was_bad = 1 if (c0 > 0 and c1 > 0) else 0

            if r == 0:
                c0 += 1
            else:
                c1 += 1

            now_bad = 1 if (c0 > 0 and c1 > 0) else 0
            if now_bad != was_bad:
                badrows += now_bad - was_bad

            rowcnt[x] = (c0 << SHIFT) | c1

    def remove_row(x, r):
        nonlocal crows, badrows
        p = rowcnt[x]
        c0 = p >> SHIFT
        c1 = p & MASK
        was_bad = 1 if (c0 > 0 and c1 > 0) else 0

        if r == 0:
            c0 -= 1
        else:
            c1 -= 1

        now_bad = 1 if (c0 > 0 and c1 > 0) else 0
        if now_bad != was_bad:
            badrows += now_bad - was_bad

        if c0 + c1 == 0:
            del rowcnt[x]
            crows -= 1
        else:
            rowcnt[x] = (c0 << SHIFT) | c1

    answers = []

    for _ in range(k):
        x = next(it)
        y = next(it)
        t = next(it)

        key = (x << SHIFT) | y
        prev = current.get(key, -1)

        if prev != t:
            px = (x - 1) & 1
            py = (y - 1) & 1

            if prev != -1:
                remove_col(y, prev ^ px)
                remove_row(x, prev ^ py)

                b = prev ^ px ^ py
                if b == 0:
                    base0 -= 1
                else:
                    base1 -= 1

            if t != -1:
                add_col(y, t ^ px)
                add_row(x, t ^ py)

                b = t ^ px ^ py
                if b == 0:
                    base0 += 1
                else:
                    base1 += 1

                current[key] = t
            else:
                if prev != -1:
                    del current[key]

        if badcols == 0:
            type_a = pow2[m - ccols]
        else:
            type_a = 0

        if badrows == 0:
            type_b = pow2[n - crows]
        else:
            type_b = 0

        if base0 > 0 and base1 > 0:
            intersection = 0
        elif base0 + base1 == 0:
            intersection = 2
        else:
            intersection = 1

        answers.append(str((type_a + type_b - intersection) % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()