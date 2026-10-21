import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    possible = (1 << 26) - 1
    ans = 0
    pos = 1

    # The last action is the correct guess, so it cannot cause an excessive shock.
    for _ in range(n - 1):
        action = data[pos]
        word = data[pos + 1]
        pos += 2

        if possible.bit_count() == 1:
            if action == b'!':
                ans += 1
            elif action == b'?':
                ans += 1

        if action == b'!':
            word_mask = 0
            for ch in word:
                word_mask |= 1 << (ch - ord('a'))
            possible &= word_mask

        elif action == b'.':
            word_mask = 0
            for ch in word:
                word_mask |= 1 << (ch - ord('a'))
            possible &= ~word_mask

        else:  # action == b'?'
            guessed = word[0] - ord('a')
            possible &= ~(1 << guessed)

    print(ans)


if __name__ == "__main__":
    main()