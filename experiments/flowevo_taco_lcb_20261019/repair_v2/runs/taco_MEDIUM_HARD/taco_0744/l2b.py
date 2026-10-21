import sys
from collections import defaultdict

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    if k == 1:
        powers = [1]
    elif k == -1:
        powers = [1, -1]
    else:
        limit = sum(abs(x) for x in a)
        powers = []
        value = 1
        while True:
            powers.append(value)
            value *= k
            if abs(value) > limit:
                break

    freq = defaultdict(int)
    freq[0] = 1

    prefix = 0
    answer = 0

    for x in a:
        prefix += x

        for power in powers:
            answer += freq.get(prefix - power, 0)

        freq[prefix] += 1

    print(answer)

if __name__ == "__main__":
    main()