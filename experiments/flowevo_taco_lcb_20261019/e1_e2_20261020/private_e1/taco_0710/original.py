import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    possible = (1 << 26) - 1
    answer = 0

    idx = 1
    for _ in range(n - 1):
        op = data[idx][0]
        word = data[idx + 1]
        idx += 2

        if possible.bit_count() == 1 and (op == ord('!') or op == ord('?')):
            answer += 1

        if op == ord('.'):
            for ch in word:
                possible &= ~(1 << (ch - ord('a')))
        elif op == ord('!'):
            seen = 0
            for ch in word:
                seen |= 1 << (ch - ord('a'))
            possible &= seen
        else:  # op == ord('?')
            possible &= ~(1 << (word[0] - ord('a')))

    print(answer)


if __name__ == "__main__":
    main()