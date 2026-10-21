import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    size = len(data)
    idx = 0

    def next_int() -> int:
        nonlocal idx

        while idx < size and data[idx] <= 32:
            idx += 1

        num = 0
        while idx < size and 48 <= data[idx] <= 57:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()

        # pref_even[i] = number of even elements in A[1..i]
        pref_even = [0] * (n + 1)

        for i in range(1, n + 1):
            value = next_int()
            pref_even[i] = pref_even[i - 1] + (1 if value % 2 == 0 else 0)

        q = next_int()

        for _ in range(q):
            left = next_int()
            right = next_int()

            even_count = pref_even[right] - pref_even[left - 1]

            # Bitwise AND is odd iff every number in the range is odd.
            # If there is at least one even number, the AND is even.
            if even_count == 0:
                answers.append("ODD")
            else:
                answers.append("EVEN")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()