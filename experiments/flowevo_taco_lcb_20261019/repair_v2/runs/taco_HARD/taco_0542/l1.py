import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    max_a = max(a)

    present = bytearray(max_a + 1)
    for v in a:
        present[v] = 1

    prev_present = [0] * (max_a + 1)
    last = 0
    for i in range(1, max_a + 1):
        if present[i]:
            last = i
        prev_present[i] = last

    ans = 0
    M = max_a

    for x in range(M, 0, -1):
        if x - 1 <= ans:
            break

        if not present[x]:
            continue

        cur = ans

        for low in range(x, M + 1, x):
            right = low + x - 1
            if right > M:
                right = M

            v = prev_present[right]
            if v >= low:
                rem = v - low
                if rem > cur:
                    cur = rem
                    if cur == x - 1:
                        break

        ans = cur

    sys.stdout.write(str(ans))


if __name__ == "__main__":
    solve()