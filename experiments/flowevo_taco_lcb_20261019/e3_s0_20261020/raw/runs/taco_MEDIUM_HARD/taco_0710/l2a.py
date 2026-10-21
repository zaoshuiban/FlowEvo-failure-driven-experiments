import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    possible = (1 << 26) - 1
    answer = 0

    idx = 1
    for i in range(n):
        action = data[idx]
        word = data[idx + 1]
        idx += 2

        is_last = (i == n - 1)

        # If the selected letter was already uniquely determined before this action,
        # then shocks from non-final '!' and '?' actions are excessive.
        if possible.bit_count() == 1 and not is_last:
            if action == b'!' or action == b'?':
                answer += 1

        if is_last:
            break

        if action == b'!':
            mask = 0
            for ch in word:
                mask |= 1 << (ch - ord('a'))
            possible &= mask

        elif action == b'.':
            mask = 0
            for ch in word:
                mask |= 1 << (ch - ord('a'))
            possible &= ~mask

        else:  # action == b'?'
            guessed = word[0] - ord('a')
            possible &= ~(1 << guessed)

    print(answer)


if __name__ == "__main__":
    solve()