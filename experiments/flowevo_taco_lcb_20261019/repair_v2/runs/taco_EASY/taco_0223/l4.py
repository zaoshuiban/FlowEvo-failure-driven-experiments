import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    answers = []

    # The problem normally has one test case, but this loop also safely
    # handles multiple concatenated test cases until EOF.
    while idx < len(data):
        n = data[idx]
        idx += 1

        arr = [0] * (n + 1)
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

        for i in range(1, n + 1):
            value = data[idx]
            idx += 1
            arr[i] = value
            if value % 2 == 0:
                add(i, 1)

        q = data[idx]
        idx += 1

        for _ in range(q):
            query_type = data[idx]
            x = data[idx + 1]
            y = data[idx + 2]
            idx += 3

            if query_type == 0:
                old_even = arr[x] % 2 == 0
                new_even = y % 2 == 0

                if old_even and not new_even:
                    add(x, -1)
                elif not old_even and new_even:
                    add(x, 1)

                arr[x] = y

            elif query_type == 1:
                even_count = prefix_sum(y) - prefix_sum(x - 1)
                answers.append(str(even_count))

            else:  # query_type == 2
                even_count = prefix_sum(y) - prefix_sum(x - 1)
                odd_count = (y - x + 1) - even_count
                answers.append(str(odd_count))

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()