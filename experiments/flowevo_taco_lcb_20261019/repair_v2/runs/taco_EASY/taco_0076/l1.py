from math import comb
from functools import lru_cache

# Bell numbers, extended as needed
Bell = [1]

def ensure_bell(n):
    while len(Bell) <= n:
        idx = len(Bell)
        val = 0
        for k in range(idx):
            val += comb(idx - 1, k) * Bell[k]
        Bell.append(val)

_coeff_cache = {}

def coefficients(length):
    if length in _coeff_cache:
        return _coeff_cache[length]

    ensure_bell(length)
    w = []

    for i in range(length):
        left = i
        right = length - 1 - i

        total = 0
        left_combs = [comb(left, l) for l in range(left + 1)]
        right_combs = [comb(right, r) for r in range(right + 1)]
        powers10 = [10 ** r for r in range(right + 1)]

        for l, cl in enumerate(left_combs):
            for r, cr in enumerate(right_combs):
                # This would mean all digits are in the same bucket,
                # but distributions into only one bucket are excluded.
                if l == left and r == right:
                    continue

                outside = length - 1 - l - r
                total += cl * cr * powers10[r] * Bell[outside]

        w.append(total)

    _coeff_cache[length] = w
    return w


@lru_cache(maxsize=None)
def f_value(n):
    s = str(n)
    w = coefficients(len(s))
    return sum((ord(s[i]) - 48) * w[i] for i in range(len(s)))


def digits_to_int(digits):
    value = 0
    for d in digits:
        value = value * 10 + d
    return value


def min_same_length_greater(n, target):
    s = str(n)
    m = len(s)
    digits = [ord(c) - 48 for c in s]
    w = coefficients(m)

    prefix = [0] * (m + 1)
    for i, d in enumerate(digits):
        prefix[i + 1] = prefix[i] + d * w[i]

    suffix_weight = [0] * (m + 1)
    for i in range(m - 1, -1, -1):
        suffix_weight[i] = suffix_weight[i + 1] + w[i]

    # First differing position from the right to the left,
    # so that we obtain the smallest number greater than n.
    for p in range(m - 1, -1, -1):
        base = prefix[p]
        max_after = 9 * suffix_weight[p + 1]

        for d in range(digits[p] + 1, 10):
            cur = base + d * w[p]

            if cur + max_after <= target:
                continue

            result_digits = digits[:p] + [d]
            cur2 = cur
            possible = True

            for j in range(p + 1, m):
                max_after_j = 9 * suffix_weight[j + 1]
                chosen = -1

                for nd in range(10):
                    if cur2 + nd * w[j] + max_after_j > target:
                        chosen = nd
                        cur2 += nd * w[j]
                        break

                if chosen == -1:
                    possible = False
                    break

                result_digits.append(chosen)

            if possible:
                return digits_to_int(result_digits)

    return None


def min_length_number(target, length):
    w = coefficients(length)

    suffix_weight = [0] * (length + 1)
    for i in range(length - 1, -1, -1):
        suffix_weight[i] = suffix_weight[i + 1] + w[i]

    cur = 0
    result = []

    for i in range(length):
        start = 1 if i == 0 else 0
        max_after = 9 * suffix_weight[i + 1]
        chosen = -1

        for d in range(start, 10):
            if cur + d * w[i] + max_after > target:
                chosen = d
                cur += d * w[i]
                break

        if chosen == -1:
            return None

        result.append(chosen)

    return digits_to_int(result)


def find(n, z):
    target = f_value(n) + z
    m = len(str(n))

    answer = min_same_length_greater(n, target)
    if answer is not None:
        return answer

    length = m + 1

    while True:
        w = coefficients(length)

        if 9 * sum(w) > target:
            answer = min_length_number(target, length)
            if answer is not None:
                return answer

        length += 1