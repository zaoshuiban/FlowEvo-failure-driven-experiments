import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
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
            row = next(it)
            friend_bit = 1 << i

            for j in range(k):
                if row[j] == ord('1'):
                    dish_masks[j] |= friend_bit

        all_friends = (1 << n) - 1
        min_dishes = k

        for subset in range(1 << k):
            count = subset.bit_count()
            if count >= min_dishes:
                continue

            covered = 0
            for j in range(k):
                if subset & (1 << j):
                    covered |= dish_masks[j]

            if covered == all_friends:
                min_dishes = count

        answers.append(str(min_dishes))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()