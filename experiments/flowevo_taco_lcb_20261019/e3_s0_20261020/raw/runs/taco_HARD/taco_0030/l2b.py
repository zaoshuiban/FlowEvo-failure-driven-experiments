import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    q = data[0]
    idx = 1
    answers = []

    for _ in range(q):
        n = data[idx]
        u = data[idx + 1]
        v = data[idx + 2]
        idx += 3

        # Find LCA of u and v in the infinite binary heap tree.
        a, b = u, v
        while a != b:
            if a > b:
                a //= 2
            else:
                b //= 2
        lca = a

        depth_u = u.bit_length() - 1
        depth_v = v.bit_length() - 1
        depth_lca = lca.bit_length() - 1

        up_len = depth_u - depth_lca
        down_len = depth_v - depth_lca

        up_suffix = u & ((1 << up_len) - 1)
        down_suffix = v & ((1 << down_len) - 1)

        ans = min(
            (n - up_suffix) // (1 << up_len),
            (n - down_suffix) // (1 << down_len)
        )
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()