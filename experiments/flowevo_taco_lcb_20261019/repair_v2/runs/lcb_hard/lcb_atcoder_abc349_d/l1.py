import sys

def main():
    L, R = map(int, sys.stdin.readline().split())

    ans = []
    x = L

    while x < R:
        remain = R - x
        p = 1 << (remain.bit_length() - 1)

        if x == 0:
            size = p
        else:
            lowbit = x & -x
            size = min(p, lowbit)

        ans.append((x, x + size))
        x += size

    print(len(ans))
    print("\n".join(f"{l} {r}" for l, r in ans))


if __name__ == "__main__":
    main()