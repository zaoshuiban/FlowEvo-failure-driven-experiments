```python
import sys
from array import array


def solve_case(a):
    n = len(a)
    mn = min(a)
    mx = max(a)
    max_diff = mx - mn

    # If all positions of the interval are present, answer is n.
    if n == max_diff + 1:
        return n

    d = n
    limit = min(max_diff, n + 10)
    seen = [-1] * (max_diff + 1)

    # Try a few candidates directly using residues.
    while d <= limit:
        ok = True
        for x in a:
            r = x % d
            if seen[r] == d:
                ok = False
                break
            seen[r] = d

        if ok:
            return d
        d += 1

    if d > max_diff:
        return max_diff + 1

    start = d
    remaining = max_diff - start + 1

    # If only a few candidates remain, direct checking is cheaper.
    if remaining <= 100:
        cur = start
        while cur <= max_diff:
            ok = True
            for x in a:
                r = x % cur
                if seen[r] == cur:
                    ok = False
                    break
                seen[r] = cur

            if ok:
                return cur
            cur += 1
        return max_diff + 1

    # Compute all positive pairwise differences using one big integer
    # multiplication as a convolution.
    shift = n.bit_length()
    mask = (1 << shift) - 1

    value_bytes = (max_diff * shift + 7) // 8 + 1
    p_bytes = bytearray(value_bytes)
    q_bytes = bytearray(value_bytes)

    for x in a:
        b = x - mn

        pos = b * shift
        p_bytes[pos >> 3] |= 1 << (pos & 7)

        pos = (max_diff - b) * shift
        q_bytes[pos >> 3] |= 1 << (pos & 7)

    p_int = int.from_bytes(p_bytes, "little")
    q_int = int.from_bytes(q_bytes, "little")
    prod = p_int * q_int

    coeff_count = 2 * max_diff + 1
    prod_bytes_len = (coeff_count * shift + 7) // 8 + 1
    prod_bytes = prod.to_bytes(prod_bytes_len, "little")

    coeffs = array("I", [0]) * coeff_count

    bit_buf = 0