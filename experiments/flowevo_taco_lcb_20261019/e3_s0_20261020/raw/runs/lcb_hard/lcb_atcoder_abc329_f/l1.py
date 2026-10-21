import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, Q = data[0], data[1]

    boxes = [{data[2 + i]} for i in range(N)]

    idx = 2 + N
    answers = []

    for _ in range(Q):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        idx += 2

        if len(boxes[a]) > len(boxes[b]):
            boxes[a], boxes[b] = boxes[b], boxes[a]

        smaller = boxes[a]
        larger = boxes[b]

        if smaller:
            for color in smaller:
                larger.add(color)
            smaller.clear()

        answers.append(str(len(larger)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()