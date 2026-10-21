import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    k = data[1]
    a = data[2:2 + n]

    # Maximum possible absolute value of any subarray sum.
    pref = 0
    min_pref = 0
    max_pref = 0
    for x in a:
        pref += x
        if pref < min_pref:
            min_pref = pref
        elif pref > max_pref:
            max_pref = pref

    max_abs = max_pref - min_pref

    if k == 1:
        if max_abs < 1:
            print(0)
            return

        freq = {0: 1}
        s = 0
        ans = 0
        get = freq.get

        for x in a:
            s += x
            ans += get(s - 1, 0)
            freq[s] = get(s, 0) + 1

        print(ans)
        return

    if k == -1:
        if max_abs < 1:
            print(0)
            return

        freq = {0: 1}
        s = 0
        ans = 0
        get = freq.get

        for x in a:
            s += x
            ans += get(s - 1, 0) + get(s + 1, 0)
            freq[s] = get(s, 0) + 1

        print(ans)
        return

    if k == 0:
        # Powers of 0 are 1 (0^0) and 0 (0^p for p >= 1).
        freq = {0: 1}
        s = 0
        ans = 0
        get = freq.get

        for x in a:
            s += x
            ans += get(s, 0) + get(s - 1, 0)
            freq[s] = get(s, 0) + 1

        print(ans)
        return

    powers = []
    value = 1

    if k > 1:
        while value <= max_abs:
            powers.append(value)
            value *= k
    else:  # k < -1
        while abs(value) <= max_abs:
            powers.append(value)
            value *= k

    if not powers:
        print(0)
        return

    powers = tuple(powers)

    freq = {0: 1}
    s = 0
    ans = 0
    get = freq.get

    for x in a:
        s += x

        for p in powers:
            ans += get(s - p, 0)

        freq[s] = get(s, 0) + 1

    print(ans)


if __name__ == "__main__":
    main()