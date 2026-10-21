import sys

def solve():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        n = len(s)
        z = s.count(b'0')
        o = n - z

        if z == 0:
            answers.append("0")
            continue

        # Count ones in the first window of length z: s[0:z]
        ones = 0
        for i in range(z):
            if s[i] == 49:  # ord('1')
                ones += 1

        min_ones = ones

        # Slide window of length z over all possible starts 0..o
        for start in range(1, o + 1):
            if s[start - 1] == 49:
                ones -= 1
            if s[start + z - 1] == 49:
                ones += 1
            if ones < min_ones:
                min_ones = ones

        answers.append(str(min_ones))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()