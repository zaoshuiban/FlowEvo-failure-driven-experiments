import sys
from bisect import bisect_left


def solve() -> None:
    input = sys.stdin.buffer.readline

    first = input().split()
    if not first:
        return

    n, m = map(int, first)
    s = input().strip()

    positions = [[] for _ in range(256)]
    for i, ch in enumerate(s):
        positions[ch].append(i)

    parent = [None] * 256
    for c in range(256):
        sz = len(positions[c])
        parent[c] = list(range(sz + 1))

    bit = [0] * (n + 1)
    for i in range(1, n + 1):
        bit[i] += 1
        j = i + (i & -i)
        if j <= n:
            bit[j] += bit[i]

    top_power = 1 << (n.bit_length() - 1)

    def kth(k: int) -> int:
        idx = 0
        bitmask = top_power
        while bitmask:
            nxt = idx + bitmask
            if nxt <= n and bit[nxt] < k:
                k -= bit[nxt]
                idx = nxt
            bitmask >>= 1
        return idx

    def remove_position(pos: int) -> None:
        i = pos + 1
        while i <= n:
            bit[i] -= 1
            i += i & -i

    def find(par, x: int) -> int:
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    alive = bytearray([1]) * n
    length = n

    for _ in range(m):
        if length == 0:
            break

        parts = input().split()
        l = int(parts[0])
        r = int(parts[1])
        c = parts[2][0]

        left_original = kth(l)
        right_original = kth(r)

        arr = positions[c]
        par = parent[c]

        idx = bisect_left(arr, left_original)
        idx = find(par, idx)
        sz = len(arr)

        while idx < sz and arr[idx] <= right_original:
            pos = arr[idx]
            alive[pos] = 0
            remove_position(pos)
            length -= 1

            par[idx] = find(par, idx + 1)
            idx = par[idx]

    result = bytearray()
    for i in range(n):
        if alive[i]:
            result.append(s[i])

    sys.stdout.buffer.write(result)
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    solve()