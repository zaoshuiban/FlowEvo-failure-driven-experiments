import sys

def can_make(a, k):
    a = a[:]
    while any(a):
        count = 0
        for i in range(len(a)):
            quotient, remainder = divmod(a[i], k)
            a[i] = quotient

            if remainder > 1:
                return False
            if remainder == 1:
                count += 1

        if count > 1:
            return False

    return True


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        a = [next(it) for _ in range(n)]

        answers.append("YES" if can_make(a, k) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()