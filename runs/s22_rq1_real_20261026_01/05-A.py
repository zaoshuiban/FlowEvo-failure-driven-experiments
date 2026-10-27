import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    q = int(data[1])
    queries = [int(x) for x in data[2:2+q]]

    out = []
    for x in queries:
        # Determine value at final position x (1-indexed).
        # Odd positions: value = (x+1)//2.
        # Even positions: value = k + f(m, x//2), where k = ceil(n/2), m = n - k,
        # and f(m, y) is the value at position y in the final array for size m.
        # We compute f recursively/iteratively.
        pos = x
        offset = 0
        cur_n = n
        while True:
            if pos % 2 == 1:
                out.append(offset + (pos + 1) // 2)
                break
            k = (cur_n + 1) // 2  # ceil(cur_n/2)
            m = cur_n - k
            offset += k
            pos //= 2
            cur_n = m
            if cur_n == 0:
                # Should not happen for valid pos, but safeguard
                out.append(offset)
                break

    sys.stdout.write("\n".join(map(str, out)))

if __name__ == "__main__":
    solve()