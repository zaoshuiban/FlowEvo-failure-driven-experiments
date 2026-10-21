import sys


def construct(n: int):
    if n == 1:
        return [0]

    # Largest power of two strictly smaller than n
    L = 1 << ((n - 1).bit_length() - 1)
    m = n - L

    upper_half_pattern = construct(m)
    cross = upper_half_pattern[-1]

    result = [L + x for x in upper_half_pattern]

    for i in range(L):
        gray = i ^ (i >> 1)
        result.append(gray ^ cross)

    return result


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    answers = []

    for idx in range(1, t + 1):
        n = data[idx]
        seq = construct(n)
        answers.append(" ".join(map(str, seq)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()