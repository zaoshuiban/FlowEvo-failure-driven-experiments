import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    ans = []

    for _ in range(t):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2

        # By Bertrand's Ballot Theorem:
        # P(Lalit remains strictly ahead throughout) = (a - b) / (a + b)
        if a > b:
            prob = (a - b) / (a + b)
        else:
            prob = 0.0

        ans.append(f"{prob:.12f}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()