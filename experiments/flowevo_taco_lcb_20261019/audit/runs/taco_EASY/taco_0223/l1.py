import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    arr = [0] * (n + 1)
    bit = [0] * (n + 1)

    def add(index, value):
        while index <= n:
            bit[index] += value
            index += index & -index

    def prefix_sum(index):
        total = 0
        while index > 0:
            total += bit[index]
            index -= index & -index
        return total

    for i in range(1, n + 1):
        value = next(it)
        arr[i] = value
        if value % 2 == 0:
            add(i, 1)

    q = next(it)
    answers = []

    for _ in range(q):
        query_type = next(it)
        x = next(it)
        y = next(it)

        if query_type == 0:
            old_value = arr[x]
            arr[x] = y

            old_even = 1 if old_value % 2 == 0 else 0
            new_even = 1 if y % 2 == 0 else 0

            if old_even != new_even:
                add(x, new_even - old_even)

        elif query_type == 1:
            even_count = prefix_sum(y) - prefix_sum(x - 1)
            answers.append(str(even_count))

        else:
            total_count = y - x + 1
            even_count = prefix_sum(y) - prefix_sum(x - 1)
            odd_count = total_count - even_count
            answers.append(str(odd_count))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()