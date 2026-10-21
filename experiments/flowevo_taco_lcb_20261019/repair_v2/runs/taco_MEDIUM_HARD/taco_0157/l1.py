import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1

        count_a = 0
        total_a = 0
        total_b = 0
        pairs_in_one = 0

        for ch in s:
            if ch == 97:  # 'a'
                count_a += 1
                total_a += 1
            elif ch == 98:  # 'b'
                pairs_in_one += count_a
                total_b += 1

        answer = k * pairs_in_one
        answer += total_a * total_b * k * (k - 1) // 2

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()