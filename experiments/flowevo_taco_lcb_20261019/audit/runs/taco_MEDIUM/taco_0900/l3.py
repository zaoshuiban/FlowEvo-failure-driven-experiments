import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        return

    idx = 0
    size = len(data)

    def next_int() -> int:
        nonlocal idx

        while idx < size and data[idx] <= 32:
            idx += 1

        sign = 1
        if idx < size and data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < size and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()

        # prefix_odd[i] = number of odd elements among A[1..i]
        prefix_odd = [0] * (n + 1)

        for i in range(1, n + 1):
            value = next_int()
            prefix_odd[i] = prefix_odd[i - 1] + (value & 1)

        q = next_int()

        for _ in range(q):
            left = next_int()
            right = next_int()

            odd_count = prefix_odd[right] - prefix_odd[left - 1]
            length = right - left + 1

            # Bitwise AND is odd iff every number in the range is odd.
            if odd_count == length:
                answers.append("ODD")
            else:
                answers.append("EVEN")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()