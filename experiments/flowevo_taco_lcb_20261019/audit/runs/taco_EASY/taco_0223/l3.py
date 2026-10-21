import sys


def process_case(data, idx):
    n = data[idx]
    idx += 1

    if n < 0 or idx + n > len(data):
        raise ValueError

    arr = [0] * (n + 1)
    for i in range(1, n + 1):
        arr[i] = data[idx]
        idx += 1

    bit = [0] * (n + 1)

    def add(i, value):
        while i <= n:
            bit[i] += value
            i += i & -i

    def prefix_sum(i):
        total = 0
        while i > 0:
            total += bit[i]
            i -= i & -i
        return total

    for i in range(1, n + 1):
        if arr[i] % 2 == 0:
            add(i, 1)

    if idx >= len(data):
        raise ValueError

    q = data[idx]
    idx += 1

    if q < 0 or idx + 3 * q > len(data):
        raise ValueError

    answers = []

    for _ in range(q):
        query_type = data[idx]
        x = data[idx + 1]
        y = data[idx + 2]
        idx += 3

        if query_type == 0:
            if not (1 <= x <= n):
                raise ValueError

            old_even = arr[x] % 2 == 0
            new_even = y % 2 == 0

            if old_even and not new_even:
                add(x, -1)
            elif not old_even and new_even:
                add(x, 1)

            arr[x] = y

        elif query_type == 1:
            if not (1 <= x <= y <= n):
                raise ValueError

            even_count = prefix_sum(y) - prefix_sum(x - 1)
            answers.append(str(even_count))

        elif query_type == 2:
            if not (1 <= x <= y <= n):
                raise ValueError

            even_count = prefix_sum(y) - prefix_sum(x - 1)
            odd_count = (y - x + 1) - even_count
            answers.append(str(odd_count))

        else:
            raise ValueError

    return idx, answers


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    # Normal single test case, as described in the problem statement.
    try:
        idx, answers = process_case(data, 0)
        if idx == len(data):
            output = "\n".join(answers)
            if output:
                sys.stdout.write(output + "\n")
            return
    except Exception:
        pass

    # Fallback: accept inputs with an explicit test-case count.
    try:
        t = data[0]
        if t < 0:
            raise ValueError

        idx = 1
        all_answers = []

        for _ in range(t):
            idx, answers = process_case(data, idx)
            all_answers.extend(answers)

        if idx == len(data):
            output = "\n".join(all_answers)
            if output:
                sys.stdout.write(output + "\n")
            return
    except Exception:
        pass

    # Last fallback: consecutive test cases until EOF.
    try:
        idx = 0
        all_answers = []

        while idx < len(data):
            idx, answers = process_case(data, idx)
            all_answers.extend(answers)

        output = "\n".join(all_answers)
        if output:
            sys.stdout.write(output + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()