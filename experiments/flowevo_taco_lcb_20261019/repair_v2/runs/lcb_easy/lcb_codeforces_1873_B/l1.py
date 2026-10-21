import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        min_pos = 0
        for i in range(1, n):
            if a[i] < a[min_pos]:
                min_pos = i

        a[min_pos] += 1

        product = 1
        for x in a:
            product *= x

        answers.append(str(product))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()