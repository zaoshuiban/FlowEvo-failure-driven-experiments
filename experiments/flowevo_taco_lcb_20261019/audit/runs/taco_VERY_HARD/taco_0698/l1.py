import sys
from collections import deque

MOD = 1_000_000_007
B = ord('B')
W = ord('W')


def count_no_b_runs(s, k):
    """
    f[i] = number of assignments for s[0:i] avoiding k consecutive B's.
    """
    n = len(s)
    f = [0] * (n + 1)
    f[0] = 1

    dq = deque([1])  # w[0] = 1, boundary before the first character
    total = 1
    cur_left = 0
    last_fixed_w = 0

    for i in range(1, n + 1):
        ch = s[i - 1]

        # w[i] = assignments where position i is W (as the last W/boundary)
        if ch != B:
            wi = f[i - 1]
        else:
            wi = 0

        dq.append(wi)
        total += wi
        if total >= MOD:
            total -= MOD

        if ch == W:
            last_fixed_w = i

        left = last_fixed_w
        tmp = i - k + 1
        if tmp > left:
            left = tmp

        while cur_left < left:
            total -= dq.popleft()
            if total < 0:
                total += MOD
            cur_left += 1

        f[i] = total

    return f


def main():
    input_data = sys.stdin.buffer
    n, k = map(int, input_data.readline().split())
    s = input_data.readline().strip()

    # Count strings avoiding k consecutive B's in all prefixes.
    pref_no_b = count_no_b_runs(s, k)

    # Build reversed string with B and W swapped, to count suffixes
    # avoiding k consecutive W's in the original string.
    rev_swapped = bytearray(n)
    for i in range(n):
        ch = s[n - 1 - i]
        if ch == B:
            rev_swapped[i] = W
        elif ch == W:
            rev_swapped[i] = B
        else:
            rev_swapped[i] = ord('X')

    pref_rev_no_b = count_no_b_runs(rev_swapped, k)

    # Bad strings:
    # 1) no k consecutive B's
    # 2) have a first occurrence of k consecutive B's, but no k consecutive W's after it
    bad = pref_no_b[n]

    limit = n - k + 1

    # Fixed W count in the first possible B-block.
    fixed_w_count = 0
    for i in range(k):
        if s[i] == W:
            fixed_w_count += 1

    for a in range(1, limit + 1):
        if fixed_w_count == 0:
            if a == 1:
                suffix_len = n - a - k + 1
                bad += pref_rev_no_b[suffix_len]
                if bad >= MOD:
                    bad -= MOD
            else:
                # Position a - 1 must be W, so it cannot be a fixed B.
                if s[a - 2] != B:
                    prefix_ways = pref_no_b[a - 2]
                    suffix_len = n - a - k + 1
                    bad = (bad + prefix_ways * pref_rev_no_b[suffix_len]) % MOD

        # Slide the B-block window.
        if a != limit:
            if s[a - 1] == W:
                fixed_w_count -= 1
            if s[a + k - 1] == W:
                fixed_w_count += 1

    total = pow(2, s.count(b'X'), MOD)
    answer = (total - bad) % MOD
    print(answer)


if __name__ == "__main__":
    main()