import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    pos = 0
    n = int(data[pos])
    pos += 1

    matches = {}

    for _ in range(n):
        name = data[pos]
        pos += 1

        seen = set()
        length = len(name)

        for i in range(length):
            for j in range(i + 1, length + 1):
                sub = name[i:j]
                if sub in seen:
                    continue
                seen.add(sub)

                if sub in matches:
                    matches[sub][0] += 1
                else:
                    matches[sub] = [1, name]

    q = int(data[pos])
    pos += 1

    output = []

    for _ in range(q):
        query = data[pos]
        pos += 1

        if query in matches:
            count, filename = matches[query]
            output.append(str(count).encode() + b" " + filename)
        else:
            output.append(b"0 -")

    sys.stdout.buffer.write(b"\n".join(output))


if __name__ == "__main__":
    solve()