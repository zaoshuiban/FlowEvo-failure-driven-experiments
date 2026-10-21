import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    n = int(next(it))
    info = {}

    for _ in range(n):
        name = next(it)
        length = len(name)
        substrings = set()

        for i in range(length):
            for j in range(i + 1, length + 1):
                substrings.add(name[i:j])

        for sub in substrings:
            if sub in info:
                count, example = info[sub]
                info[sub] = (count + 1, example)
            else:
                info[sub] = (1, name)

    q = int(next(it))
    answers = []

    for _ in range(q):
        query = next(it)
        if query in info:
            count, example = info[query]
            answers.append(str(count).encode() + b" " + example)
        else:
            answers.append(b"0 -")

    sys.stdout.buffer.write(b"\n".join(answers))


if __name__ == "__main__":
    solve()