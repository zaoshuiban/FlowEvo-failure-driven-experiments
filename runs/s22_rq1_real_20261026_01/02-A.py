import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    t = int(data[1])

    # We need count of m in [1, n] such that the sum of row m+1 equals t.
    # Row m+1 (0-indexed row m) contains values (m xor k) for k = 0..m.
    # Sum equals t iff exactly one k in [0, m] has (m xor k) = t.
    # Since xor is a bijection, k = m xor t is unique. It is in [0, m] iff
    # (m xor t) <= m. So condition: (m xor t) <= m.
    #
    # Fact: (m xor t) <= m iff at the highest set bit of t, m has bit 1.
    # (For t >= 1.) Let b = highest set bit of t. Then m must have bit b set.
    #
    # So answer = count of m in [1, n] with bit b set.
    # Note: no need for m >= t separately; if m has bit b set and b is highest
    # bit of t, then m >= 2^b, but t could be larger than m? If m has bit b set
    # and t has bit b set, m could still be less than t (e.g., t=6 (110), m=4 (100)).
    # Check condition (m xor t) <= m for m=4, t=6: 4 xor 6 = 2 <= 4, true.
    # So m need not be >= t. The condition is exactly bit b of m is 1.
    # Let's verify: t=6 (110), b=2. m=4 (100) has bit 2 set, xor=2<=4 true.
    # m=5 (101) bit 2 set, xor=3<=5 true. m=7 (111) bit 2 set, xor=1<=7 true.
    # m=2 (010) bit 2 not set, xor=4 > 2 false. Good.
    #
    # So answer = count of m in [1, n] with bit b set.

    b = t.bit_length() - 1
    mask = 1 << b

    def count_bit_set(x, bit):
        # count numbers in [0, x] with given bit set
        if x < 0:
            return 0
        cycle = 1 << (bit + 1)
        half = 1 << bit
        full = (x + 1) // cycle * half
        rem = (x + 1) % cycle
        full += max(0, rem - half)
        return full

    ans = count_bit_set(n, b) - count_bit_set(0, b)
    print(ans)

if __name__ == "__main__":
    solve()