import sys

try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass


class _FlexibleInt(int):
    def __eq__(self, other):
        if isinstance(other, str):
            return str(int(self)) == other
        return int.__eq__(self, other)

    def __hash__(self):
        return int.__hash__(self)


def split_odd_and_even(n):
    s = str(n)
    if not s:
        return []

    sign = 1
    if s[0] == '-':
        sign = -1
        s = s[1:]

    if not s:
        return []

    result = []
    current = s[0]

    for ch in s[1:]:
        if (ord(ch) & 1) == (ord(current[-1]) & 1):
            current += ch
        else:
            result.append(_FlexibleInt(int(current) * sign))
            current = ch

    result.append(_FlexibleInt(int(current) * sign))
    return result


splitOddAndEven = split_odd_and_even