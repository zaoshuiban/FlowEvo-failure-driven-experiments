import sys


def sansaXor(arr):
    n = len(arr)

    if n % 2 == 0:
        return 0

    result = 0
    for i in range(0, n, 2):
        result ^= arr[i]

    return result


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        answers.append(str(sansaXor(arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()