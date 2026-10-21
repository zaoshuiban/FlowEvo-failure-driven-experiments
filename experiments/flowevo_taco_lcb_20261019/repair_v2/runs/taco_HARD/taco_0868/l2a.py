import sys
import math

def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    t = int(data[0])
    ans = []
    for i in range(1, t + 1):
        n = int(data[i])
        result = math.cos(math.pi / (4 * n)) / math.sin(math.pi / (2 * n))
        ans.append(f"{result:.12f}")
    print("\n".join(ans))

if __name__ == "__main__":
    solve()