import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for n in data[1:1 + t]:
        if n & 1:  # n is odd
            # Odd positions are winning only for 1 or Mersenne numbers: 2^k - 1
            if n == 1 or (n & (n + 1)) == 0:
                ans.append("Alice")
            else:
                ans.append("Bob")
        else:
            if n % 4 == 0:
                # v2(n) >= 2, always winning
                ans.append("Alice")
            else:
                # v2(n) == 1, losing iff n/2 is Mersenne
                m = n // 2
                if (m & (m + 1)) == 0:
                    ans.append("Bob")
                else:
                    ans.append("Alice")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()