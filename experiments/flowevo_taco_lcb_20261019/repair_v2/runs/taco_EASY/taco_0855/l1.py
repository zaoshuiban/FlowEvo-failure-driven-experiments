import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    q = data[0]
    ans = []
    idx = 1

    for _ in range(q):
        c, m, x = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        ans.append(str(min((c + m + x) // 3, min(c, m))))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()