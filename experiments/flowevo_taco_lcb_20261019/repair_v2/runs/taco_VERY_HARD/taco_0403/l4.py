import sys


def valid_mod(arr, d):
    """Return True iff all arr elements have distinct residues modulo d."""
    seen = set()
    for x in arr:
        r = x % d
        if r in seen:
            return False
        seen.add(r)
    return True


def direct_has_diff(arr, n, max_diff):
    """For small n, directly mark all positive pairwise differences."""
    a = sorted(arr)
    has = bytearray(max_diff + 1)

    for i in range(1, n):
        ai = a[i]
        for j in range(i):
            has[ai - a[j]] = 1

    return has


def convolution_has_diff(arr, n, max_diff, mn):
    """
    Use one big integer multiplication as a convolution to mark all positive
    pairwise differences.
    """
    bits = n.bit_length()  # base = 2^bits, and base > n, so no carry
    byte_len = (max_diff * bits) // 8 + 1

    p_bytes = bytearray(byte_len)
    q_bytes = bytearray(byte_len)

    for val in arr:
        b = val - mn

        pos = b * bits
        p_bytes[pos >> 3] |= 1 << (pos & 7)

        pos = (max_diff - b) * bits
        q_bytes[pos >> 3] |= 1 << (pos & 7)

    p = int.from_bytes(p_bytes, "little")
    q = int.from_bytes(q_bytes, "little")

    prod = p * q

    mask = (1 << bits) - 1
    total_slots = 2 * max_diff + 1
    prod_len = ((total_slots * bits + 7) >> 3) + 1
    prod_bytes = prod.to_bytes(prod_len, "little")

    has = bytearray(max_diff + 1)

    buf = 0
    buf_bits = 0
    idx = 0

    for k in range(total_slots):
        while buf_bits < bits:
            buf |= prod_bytes[idx] << buf_bits
            idx += 1
            buf_bits += 8

        coeff = buf & mask
        buf >>= bits
        buf_bits -= bits

        if k > max_diff and coeff:
            has[k - max_diff] = 1

    return has


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ptr = 1
    answers = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        arr = data[ptr:ptr + n]
        ptr += n

        mn = min(arr)
        mx = max(arr)
        max_diff = mx - mn

        # If the array occupies every integer in [mn, mx], answer is n.
        if n == max_diff + 1:
            answers.append(str(n))
            continue

        ans = None

        # If only a few candidates remain, check them directly.
        if max_diff + 1 - n <= 50:
            for d in range(n, max_diff + 2):
                if valid_mod(arr, d):
                    ans = d
                    break
            answers.append(str(ans))
            continue

        # Try a few small candidates first.
        upper = min(max_diff + 2, n + 5)
        for d in range(n, upper):
            if valid_mod(arr, d):
                ans = d
                break

        if ans is not None:
            answers.append(str(ans))
            continue

        # Compute which positive differences occur.
        if n <= 700:
            has_diff = direct_has_diff(arr, n, max_diff)
        else:
            has_diff = convolution_has_diff(arr, n, max_diff, mn)

        start_d = upper

        for d in range(start_d, max_diff + 1):
            ok = True

            for x in range(d, max_diff + 1, d):
                if has_diff[x]:
                    ok = False
                    break

            if ok:
                ans = d
                break

        if ans is None:
            ans = max_diff + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()