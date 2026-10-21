import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    A = data[1:1 + m]
    B = data[1 + m:1 + 2 * m]

    A.sort()

    order = sorted(range(m), key=lambda i: B[i], reverse=True)

    answer = [0] * m
    for value, index in zip(A, order):
        answer[index] = value

    sys.stdout.write(" ".join(map(str, answer)))

if __name__ == "__main__":
    main()