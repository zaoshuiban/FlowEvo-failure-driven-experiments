import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    p = int(data[1])

    # For the given constraints, if a solution exists, one exists with
    # at most 30 summands.  100 is a safe upper bound.
    for k in range(1, 100):
        s = n - k * p

        if s <= 0:
            # For p > 0, increasing k only makes s smaller.
            # For p <= 0, this cannot happen for positive n.
            break

        ones = bin(s).count("1")

        if ones <= k <= s:
            print(k)
            return

    print(-1)

if __name__ == "__main__":
    solve()