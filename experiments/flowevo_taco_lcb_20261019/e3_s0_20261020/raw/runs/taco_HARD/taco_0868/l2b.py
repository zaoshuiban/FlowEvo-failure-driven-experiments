import sys
import math

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    ans = []
    for i in range(1, t + 1):
        n = int(data[i])
        res = 1.0 / (2.0 * math.sin(math.pi / (4.0 * n)))
        ans.append(f"{res:.10f}")
    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()