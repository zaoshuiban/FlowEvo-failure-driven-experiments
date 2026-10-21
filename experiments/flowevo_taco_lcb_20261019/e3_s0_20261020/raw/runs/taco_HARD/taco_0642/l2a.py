import sys

MOD = 1000000007

def solve() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        return

    newline = data.find(b'\n')
    if newline == -1:
        parts = data.split()
        n = int(parts[0])
        m = sum(tok == b'1' for tok in parts[1:n + 1])
    else:
        n = int(data[:newline])
        m = data[newline + 1:].count(b'1')

    # I[m] = number of involutions on m elements:
    # I[0] = I[1] = 1
    # I[i] = I[i - 1] + (i - 1) * I[i - 2]
    if m == 0:
        involutions = 1
    else:
        prev2 = 1  # I[0]
        prev1 = 1  # I[1]
        for i in range(2, m + 1):
            cur = (prev1 + (i - 1) * prev2) % MOD
            prev2, prev1 = prev1, cur
        involutions = prev1

    # Answer = (n! / m!) * I[m] = product(m + 1 ... n) * I[m]
    ans = involutions
    for i in range(m + 1, n + 1):
        ans = ans * i % MOD

    print(ans)


if __name__ == "__main__":
    solve()