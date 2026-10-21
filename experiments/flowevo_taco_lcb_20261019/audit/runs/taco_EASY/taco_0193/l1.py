import sys

def count_pretty(n: int) -> int:
    if n <= 0:
        return 0
    q, r = divmod(n, 10)
    result = q * 3
    for d in (2, 3, 9):
        if d <= r:
            result += 1
    return result

def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        l = int(data[idx])
        r = int(data[idx + 1])
        idx += 2

        ans.append(str(count_pretty(r) - count_pretty(l - 1)))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()