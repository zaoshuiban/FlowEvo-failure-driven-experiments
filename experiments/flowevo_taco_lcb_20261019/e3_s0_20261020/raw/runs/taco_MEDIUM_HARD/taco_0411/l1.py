import sys
from functools import lru_cache


def best_in_range(l: int, r: int) -> int:
    MAX_BIT = 60

    @lru_cache(None)
    def dp(pos: int, tight_l: bool, tight_r: bool):
        if pos < 0:
            return 0, 0

        l_bit = (l >> pos) & 1
        r_bit = (r >> pos) & 1

        best_pop = -1
        best_val = 0

        for bit in (0, 1):
            if tight_l and bit < l_bit:
                continue
            if tight_r and bit > r_bit:
                continue

            next_tight_l = tight_l and (bit == l_bit)
            next_tight_r = tight_r and (bit == r_bit)

            sub_pop, sub_val = dp(pos - 1, next_tight_l, next_tight_r)

            pop = sub_pop + bit
            val = (bit << pos) + sub_val

            if pop > best_pop or (pop == best_pop and val < best_val):
                best_pop = pop
                best_val = val

        return best_pop, best_val

    return dp(MAX_BIT, True, True)[1]


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    answers = []
    idx = 1

    for _ in range(n):
        l = data[idx]
        r = data[idx + 1]
        idx += 2
        answers.append(str(best_in_range(l, r)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()