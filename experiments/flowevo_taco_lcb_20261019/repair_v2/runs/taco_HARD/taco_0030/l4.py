import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    q = data[0]
    idx = 1
    answers = []

    for _ in range(q):
        n, u, v = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        du0 = u.bit_length() - 1
        dv0 = v.bit_length() - 1

        uu, vv = u, v
        du, dv = du0, dv0

        while du > dv:
            uu >>= 1
            du -= 1
        while dv > du:
            vv >>= 1
            dv -= 1
        while uu != vv:
            uu >>= 1
            vv >>= 1
            du -= 1
            dv -= 1

        lca = uu
        dl = lca.bit_length() - 1

        a = du0 - dl
        b = dv0 - dl

        suffix_u = u - (lca << a)
        suffix_v = v - (lca << b)

        power_u = 1 << a
        power_v = 1 << b

        ans_u = (n - suffix_u) // power_u
        ans_v = (n - suffix_v) // power_v

        answers.append(str(min(ans_u, ans_v)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()