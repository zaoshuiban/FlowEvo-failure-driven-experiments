import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    A = data[1:1 + m]
    B = data[1 + m:1 + 2 * m]

    A.sort()

    indices = list(range(m))
    indices.sort(key=lambda i: B[i], reverse=True)

    answer = [0] * m

    for a, i in zip(A, indices):
        answer[i] = a

    print(*answer)

if __name__ == "__main__":
    main()