import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)

    n = next(it)
    arr = [0] + [next(it) for _ in range(n)]

    bit = [0] * (n + 1)

    def add(idx, value):
        while idx <= n:
            bit[idx] += value
            idx += idx & -idx

    def query(idx):
        total = 0
        while idx > 0:
            total += bit[idx]
            idx -= idx & -idx
        return total

    for i in range(1, n + 1):
        if arr[i] % 2 == 0:
            add(i, 1)

    q = next(it)
    answers = []

    for _ in range(q):
        query_type = next(it)
        x = next(it)
        y = next(it)

        if query_type == 0:
            old_value = arr[x]
            new_value = y

            old_even = old_value % 2 == 0
            new_even = new_value % 2 == 0

            if old_even and not new_even:
                add(x, -1)
            elif not old_even and new_even:
                add(x, 1)

            arr[x] = new_value

        elif query_type == 1:
            even_count = query(y) - query(x - 1)
            answers.append(str(even_count))

        else:
            even_count = query(y) - query(x - 1)
            total_numbers = y - x + 1
            odd_count = total_numbers - even_count
            answers.append(str(odd_count))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()