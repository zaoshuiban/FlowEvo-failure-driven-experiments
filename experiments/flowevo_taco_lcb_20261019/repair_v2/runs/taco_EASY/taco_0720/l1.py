import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    q = int(data[0])
    idx = 1
    users = {}  # current handle -> original handle

    for _ in range(q):
        old = data[idx]
        new = data[idx + 1]
        idx += 2

        if old in users:
            original = users.pop(old)
            users[new] = original
        else:
            users[new] = old

    result = [str(len(users))]
    for current, original in users.items():
        result.append(f"{original} {current}")

    sys.stdout.write("\n".join(result))

if __name__ == "__main__":
    main()