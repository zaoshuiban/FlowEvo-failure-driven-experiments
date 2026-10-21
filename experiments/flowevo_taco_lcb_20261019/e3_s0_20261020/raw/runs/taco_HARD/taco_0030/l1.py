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

        su = bin(u)[3:]
        sv = bin(v)[3:]

        common = 0
        limit = min(len(su), len(sv))
        while common < limit and su[common] == sv[common]:
            common += 1

        left_suffix = su[common:]
        right_suffix = sv[common:]

        len_a = len(left_suffix)
        len_b = len(right_suffix)

        val_a = int(left_suffix, 2) if len_a else 0
        val_b = int(right_suffix, 2) if len_b else 0

        total = 0

        for m in range(n.bit_length() + 1):
            max_p = (1 << m) - 1

            base_a = 1 << (m + len_a)
            if base_a + val_a <= n:
                upper_a = (n - base_a - val_a) >> len_a
                if upper_a > max_p:
                    upper_a = max_p
            else:
                upper_a = -1

            base_b = 1 << (m + len_b)
            if base_b + val_b <= n:
                upper_b = (n - base_b - val_b) >> len_b
                if upper_b > max_p:
                    upper_b = max_p
            else:
                upper_b = -1

            upper = upper_a if upper_a < upper_b else upper_b
            if upper >= 0:
                total += upper + 1

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()