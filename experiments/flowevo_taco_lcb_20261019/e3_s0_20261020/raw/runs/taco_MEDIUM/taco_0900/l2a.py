import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        prefix_even = [0] * (n + 1)
        for i in range(1, n + 1):
            prefix_even[i] = prefix_even[i - 1] + (arr[i - 1] % 2 == 0)

        q = data[idx]
        idx += 1

        for _ in range(q):
            l = data[idx]
            r = data[idx + 1]
            idx += 2

            even_count = prefix_even[r] - prefix_even[l - 1]

            if even_count == 0:
                answers.append("ODD")
            else:
                answers.append("EVEN")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()