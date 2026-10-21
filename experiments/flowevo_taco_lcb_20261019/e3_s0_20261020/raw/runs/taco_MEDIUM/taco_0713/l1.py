import sys
import math

def count_divisors(x: int) -> int:
    count = 0
    root = math.isqrt(x)

    for i in range(1, root + 1):
        if x % i == 0:
            if i * i == x:
                count += 1
            else:
                count += 2

    return count

def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = int(data[i])
        answers.append(str(count_divisors(n - 1)))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()