import sys


def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        k = int(next(it))

        dish_masks = [0] * k

        for i in range(n):
            likes = next(it)
            for j, ch in enumerate(likes):
                if ch == '1':
                    dish_masks[j] |= (1 << i)

        all_friends = (1 << n) - 1
        total_masks = 1 << k

        coverage = [0] * total_masks
        minimum_dishes = k + 1

        for mask in range(1, total_masks):
            last_bit = mask & -mask
            dish_index = last_bit.bit_length() - 1
            previous_mask = mask ^ last_bit

            coverage[mask] = coverage[previous_mask] | dish_masks[dish_index]

            if coverage[mask] == all_friends:
                minimum_dishes = min(minimum_dishes, mask.bit_count())

        answers.append(str(minimum_dishes))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()