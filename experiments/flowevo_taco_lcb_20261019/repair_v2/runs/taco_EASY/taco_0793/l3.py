import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    A = data[1:1 + m]
    B = data[1 + m:1 + 2 * m]

    A.sort()

    order = list(range(m))
    order.sort(key=lambda i: B[i], reverse=True)

    answer = [0] * m
    for a, idx in zip(A, order):
        answer[idx] = a

    sys.stdout.write(" ".join(map(str, answer)))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()