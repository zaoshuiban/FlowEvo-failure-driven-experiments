import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    q = data[0]
    idx = 1
    answers = []

    for _ in range(q):
        n, u, v = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        a, b = u, v
        while a != b:
            if a > b:
                a >>= 1
            else:
                b >>= 1

        lca = a

        ku = u.bit_length() - lca.bit_length()
        kv = v.bit_length() - lca.bit_length()

        pu = 1 << ku
        pv = 1 << kv

        ru = u - (lca << ku)
        rv = v - (lca << kv)

        limit_u = (n - ru) // pu
        limit_v = (n - rv) // pv

        ans = min(limit_u, limit_v)
        if ans < 0:
            ans = 0

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()