import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    n = int(data[idx])
    idx += 1

    files = data[idx:idx + n]
    idx += n

    q = int(data[idx])
    idx += 1

    queries = data[idx:idx + q]

    substring_info = {}

    for name in files:
        seen = set()
        length = len(name)

        for left in range(length):
            for right in range(left + 1, length + 1):
                sub = name[left:right]

                if sub in seen:
                    continue

                seen.add(sub)

                if sub in substring_info:
                    substring_info[sub][0] += 1
                else:
                    substring_info[sub] = [1, name]

    answer = []

    for query in queries:
        info = substring_info.get(query)

        if info is None:
            answer.append(b"0 -")
        else:
            count, name = info
            answer.append(str(count).encode() + b" " + name)

    sys.stdout.buffer.write(b"\n".join(answer))


if __name__ == "__main__":
    solve()