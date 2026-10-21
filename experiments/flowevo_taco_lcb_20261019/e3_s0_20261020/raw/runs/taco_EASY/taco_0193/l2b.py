import sys

def count_pretty(n: int) -> int:
    q, r = divmod(n, 10)
    return q * 3 + sum(1 for d in (2, 3, 9) if d <= r)

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        ans.append(str(count_pretty(r) - count_pretty(l - 1)))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()