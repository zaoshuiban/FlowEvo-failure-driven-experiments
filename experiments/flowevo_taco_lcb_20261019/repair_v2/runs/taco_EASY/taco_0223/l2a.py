import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    arr = data[idx:idx + n]
    idx += n

    q = data[idx]
    idx += 1

    bit = [0] * (n + 1)

    def add(i, delta):
        while i <= n:
            bit[i] += delta
            i += i & -i

    def prefix_sum(i):
        total = 0
        while i > 0:
            total += bit[i]
            i -= i & -i
        return total

    def range_sum(l, r):
        return prefix_sum(r) - prefix_sum(l - 1)

    for i, value in enumerate(arr, 1):
        if value % 2 == 0:
            add(i, 1)

    answers = []

    for _ in range(q):
        query_type = data[idx]
        x = data[idx + 1]
        y = data[idx + 2]
        idx += 3

        if query_type == 0:
            pos = x
            new_value = y

            old_value = arr[pos - 1]
            old_even = (old_value % 2 == 0)
            new_even = (new_value % 2 == 0)

            if old_even != new_even:
                add(pos, 1 if new_even else -1)

            arr[pos - 1] = new_value

        elif query_type == 1:
            l = x
            r = y
            answers.append(str(range_sum(l, r)))

        else:
            l = x
            r = y
            total = r - l + 1
            even_count = range_sum(l, r)
            answers.append(str(total - even_count))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()