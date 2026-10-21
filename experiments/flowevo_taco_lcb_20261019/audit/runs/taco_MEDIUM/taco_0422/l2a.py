import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        half = n // 2
        ans = []

        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                diff = j - i

                if n % 2 == 1:
                    if diff <= half:
                        ans.append("1")
                    else:
                        ans.append("-1")
                else:
                    if diff < half:
                        ans.append("1")
                    elif diff == half:
                        ans.append("0")
                    else:
                        ans.append("-1")

        output.append(" ".join(ans))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()