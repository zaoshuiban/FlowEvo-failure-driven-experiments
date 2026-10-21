import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    L = [0] * n
    R = [0] * n
    row_parity = [0] * n
    diff = [0] * (n + 2)

    total_parity = 0

    for i in range(n):
        l = next(it)
        r = next(it)

        L[i] = l
        R[i] = r

        length_parity = (r - l + 1) & 1
        row_parity[i] = length_parity
        total_parity ^= length_parity

        diff[l] += 1
        diff[r + 1] -= 1

    column_parity = [0] * (n + 1)
    current = 0

    for col in range(1, n + 1):
        current += diff[col]
        column_parity[col] = current & 1

    q = next(it)
    answers = []

    for _ in range(q):
        x = next(it)
        y = next(it)

        idx = x - 1
        contains_one = 1 if L[idx] <= y <= R[idx] else 0

        parity = (
            total_parity
            ^ row_parity[idx]
            ^ column_parity[y]
            ^ contains_one
        )

        answers.append('E' if parity == 0 else 'O')

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    main()