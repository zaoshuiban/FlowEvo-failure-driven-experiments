import sys


def solve() -> None:
    tokens = iter(sys.stdin.buffer.read().split())

    n = int(next(tokens))

    counts = {}
    samples = {}

    for _ in range(n):
        filename = next(tokens)
        length = len(filename)

        substrings = set()
        for left in range(length):
            for right in range(left + 1, length + 1):
                substrings.add(filename[left:right])

        for sub in substrings:
            counts[sub] = counts.get(sub, 0) + 1
            if sub not in samples:
                samples[sub] = filename

    q = int(next(tokens))
    answers = []

    for _ in range(q):
        query = next(tokens)
        count = counts.get(query, 0)

        if count == 0:
            answers.append(b"0 -")
        else:
            answers.append(str(count).encode() + b" " + samples[query])

    sys.stdout.buffer.write(b"\n".join(answers))


if __name__ == "__main__":
    solve()