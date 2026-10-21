import sys
import itertools

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    operations = {}
    idx = 2
    for _ in range(q):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        operations[a] = b

    alphabet = "abcdef"
    answer = 0

    for chars in itertools.product(alphabet, repeat=n):
        current = chars[0]
        possible = True

        for nxt in chars[1:]:
            result = operations.get(current + nxt)
            if result is None:
                possible = False
                break
            current = result

        if possible and current == "a":
            answer += 1

    print(answer)

if __name__ == "__main__":
    main()