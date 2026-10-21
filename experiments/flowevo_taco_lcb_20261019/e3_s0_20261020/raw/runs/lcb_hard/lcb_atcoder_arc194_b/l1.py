import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    p = data[1:1 + n]

    bit = [0] * (n + 2)
    ans = 0
    seen = 0

    for r, value in enumerate(p, 1):
        # Count previous elements <= value
        s = 0
        idx = value
        while idx > 0:
            s += bit[idx]
            idx -= idx & -idx

        greater = seen - s

        if greater:
            ans += greater * r - greater * (greater + 1) // 2

        idx = value
        while idx <= n:
            bit[idx] += 1
            idx += idx & -idx

        seen += 1

    print(ans)

if __name__ == "__main__":
    main()