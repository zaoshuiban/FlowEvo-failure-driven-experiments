import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        total_xor = 0
        for x in arr:
            total_xor ^= x

        if total_xor == 0:
            ans.append("DRAW")
            continue

        highest_bit = 1 << (total_xor.bit_length() - 1)
        cnt = 0
        for x in arr:
            if x & highest_bit:
                cnt += 1

        if cnt % 4 == 1 or (n - cnt) % 2 == 1:
            ans.append("WIN")
        else:
            ans.append("LOSE")

    sys.stdout.write("\n".join(ans) + "\n")


if __name__ == "__main__":
    solve()