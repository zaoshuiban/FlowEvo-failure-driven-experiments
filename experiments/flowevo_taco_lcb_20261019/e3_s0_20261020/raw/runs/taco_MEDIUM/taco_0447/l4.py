import sys


def is_valid_tag(tag: bytes) -> bool:
    # Minimum valid closing tag: </a>
    if len(tag) < 4:
        return False

    # Must start with "</" and end with ">"
    if tag[0] != 60 or tag[1] != 47 or tag[-1] != 62:  # ord('<'), ord('/'), ord('>')
        return False

    body = tag[2:-1]

    # Body must be non-empty
    if not body:
        return False

    # Body must contain only lowercase English letters and digits
    for ch in body:
        if not (97 <= ch <= 122 or 48 <= ch <= 57):  # 'a'-'z' or '0'-'9'
            return False

    return True


def solve() -> None:
    lines = sys.stdin.buffer.read().splitlines()
    if not lines:
        return

    idx = 0

    # Read T, skipping accidental blank lines before it if any
    while idx < len(lines) and lines[idx].strip() == b"":
        idx += 1

    if idx >= len(lines):
        return

    t = int(lines[idx].strip())
    idx += 1

    answers = []

    for _ in range(t):
        # Constraints guarantee non-empty tags, so skipping blank lines is safe.
        while idx < len(lines) and lines[idx].strip() == b"":
            idx += 1

        if idx < len(lines):
            tag = lines[idx]
            idx += 1
        else:
            tag = b""

        answers.append("Success" if is_valid_tag(tag) else "Error")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()