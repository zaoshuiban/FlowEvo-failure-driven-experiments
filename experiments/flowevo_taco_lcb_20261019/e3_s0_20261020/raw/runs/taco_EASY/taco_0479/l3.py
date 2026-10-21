import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, d = data[0], data[1]
    x = data[2:2 + n]

    # The input is guaranteed to be sorted, but sorting makes the solution robust.
    x.sort()

    answer = 0
    left = 0

    for right in range(n):
        while x[right] - x[left] > d:
            left += 1

        count = right - left
        answer += count * (count - 1) // 2

    print(answer)

if __name__ == "__main__":
    main()