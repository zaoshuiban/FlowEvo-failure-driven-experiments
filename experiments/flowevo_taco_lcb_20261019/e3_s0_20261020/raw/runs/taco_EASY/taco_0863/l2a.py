import sys
import itertools

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    rules = {}
    idx = 2

    for _ in range(q):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        rules[a] = b

    answer = 0
    letters = "abcdef"

    for chars in itertools.product(letters, repeat=n):
        s = "".join(chars)

        while len(s) > 1:
            replacement = rules.get(s[:2])
            if replacement is None:
                break
            s = replacement + s[2:]

        if s == "a":
            answer += 1

    print(answer)


if __name__ == "__main__":
    main()