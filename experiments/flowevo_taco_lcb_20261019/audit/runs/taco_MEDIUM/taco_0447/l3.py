import sys


def is_valid_tag(tag: bytes) -> bool:
    # Minimum valid tag: </a>
    if len(tag) < 4:
        return False

    # Must start with '<' '/' and end with '>'
    if tag[0] != ord('<') or tag[1] != ord('/') or tag[-1] != ord('>'):
        return False

    body = tag[2:-1]

    # Non-empty body
    if not body:
        return False

    for ch in body:
        # Allow only 'a'-'z' and '0'-'9'
        if not (ord('a') <= ch <= ord('z') or ord('0') <= ch <= ord('9')):
            return False

    return True


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        tag = data[i]
        answers.append("Success" if is_valid_tag(tag) else "Error")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()