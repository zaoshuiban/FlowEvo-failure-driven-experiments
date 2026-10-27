import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    strings = data[1:1+n]

    # For a string to be usable as the left part of a pair, it must be
    # "prefix-valid": no prefix has more ')' than '('.
    # Its balance (opens - closes) must be >= 0.
    # For the right part, reading from the right, no suffix has more '(' than ')'.
    left = {}
    right = {}

    for s in strings:
        bal = 0
        min_bal = 0
        for ch in s:
            if ch == 40:  # '('
                bal += 1
            else:
                bal -= 1
            if bal < min_bal:
                min_bal = bal

        if min_bal >= 0:
            # usable as left part; balance = bal >= 0 automatically
            left[bal] = left.get(bal, 0) + 1
        else:
            # check as right part: reverse scan
            bal2 = 0
            min_bal2 = 0
            for ch in reversed(s):
                if ch == 41:  # ')'
                    bal2 += 1
                else:
                    bal2 -= 1
                if bal2 < min_bal2:
                    min_bal2 = bal2
            if min_bal2 >= 0:
                # original balance = -bal2
                right[-bal2] = right.get(-bal2, 0) + 1

    ans = 0
    for b, cnt in left.items():
        if -b in right:
            ans += min(cnt, right[-b])

    print(ans)

if __name__ == "__main__":
    solve()