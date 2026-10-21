import sys


def main() -> None:
    input = sys.stdin.buffer.readline

    n = int(input())
    possible = [True] * 26
    determined = False
    answer = 0

    for i in range(n):
        parts = input().split()
        action = parts[0][0]
        arg = parts[1]

        is_last = (i == n - 1)

        # If the letter was already uniquely determined before this action,
        # then every shock from a non-final action is excessive.
        if determined and not is_last:
            if action == ord('!') or action == ord('?'):
                answer += 1

        # The last action is always the correct guess, so we stop here.
        if is_last:
            break

        if action == ord('.'):
            # No shock: the selected letter is not in this word.
            for ch in arg:
                possible[ch - ord('a')] = False

        elif action == ord('!'):
            # Shock: the selected letter must be in this word.
            present = set(arg)
            for idx in range(26):
                if possible[idx] and (idx + ord('a')) not in present:
                    possible[idx] = False

        else:  # action == '?'
            # Incorrect guess before the last action.
            possible[arg[0] - ord('a')] = False

        if not determined and sum(possible) == 1:
            determined = True

    print(answer)


if __name__ == "__main__":
    main()