import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        x, y = data[idx], data[idx + 1]
        idx += 2

        if y % x == 0:
            ans.append(f"1 {y // x}")
        else:
            ans.append("0 0")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()