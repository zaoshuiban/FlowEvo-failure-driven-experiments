import sys

def is_magical(n, m):
    if n == 1 or m == 1:
        return n * m == 2
    return n % 2 == 0 or m % 2 == 0

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2
        ans.append("Yes" if is_magical(n, m) else "No")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()