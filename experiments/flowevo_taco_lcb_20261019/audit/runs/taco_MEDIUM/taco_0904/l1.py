import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        idx += 2

        friends = []
        for _ in range(n):
            s = data[idx]
            idx += 1

            mask = 0
            for j, ch in enumerate(s):
                if ch == '1':
                    mask |= (1 << j)

            friends.append(mask)

        min_dishes = k

        for selected in range(1 << k):
            count = selected.bit_count()

            if count >= min_dishes:
                continue

            all_happy = True
            for friend in friends:
                if (friend & selected) == 0:
                    all_happy = False
                    break

            if all_happy:
                min_dishes = count

        answers.append(str(min_dishes))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()