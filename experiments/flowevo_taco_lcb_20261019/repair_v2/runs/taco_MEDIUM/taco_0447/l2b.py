import sys


def is_valid_tag(tag: bytes) -> bool:
    # Minimum valid tag is </a>
    if len(tag) < 4:
        return False

    if not tag.startswith(b'</') or not tag.endswith(b'>'):
        return False

    body = tag[2:-1]

    if len(body) == 0:
        return False

    for ch in body:
        if not (97 <= ch <= 122 or 48 <= ch <= 57):  # a-z or 0-9
            return False

    return True


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        tag = data[i]
        answers.append("Success" if is_valid_tag(tag) else "Error")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()