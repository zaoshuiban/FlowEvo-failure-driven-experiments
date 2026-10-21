import sys
from itertools import product

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    operations = {}
    idx = 2
    for _ in range(q):
        pair = data[idx]
        result = data[idx + 1]
        idx += 2
        operations[pair] = result

    letters = "abcdef"
    answer = 0

    for s in product(letters, repeat=n):
        current = s[0]
        possible = True

        for i in range(1, n):
            pair = current + s[i]
            if pair not in operations:
                possible = False
                break
            current = operations[pair]

        if possible and current == "a":
            answer += 1

    print(answer)


if __name__ == "__main__":
    main()