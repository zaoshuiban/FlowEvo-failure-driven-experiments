import sys


def main():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    q = int(next(it))
    current_time = 0

    plants = []
    head = 0
    answers = []

    for _ in range(q):
        query_type = next(it)

        if query_type == b"1":
            plants.append(current_time)

        elif query_type == b"2":
            t = int(next(it))
            current_time += t

        else:
            h = int(next(it))
            threshold = current_time - h

            before = head
            while head < len(plants) and plants[head] <= threshold:
                head += 1

            answers.append(str(head - before))

    print("\n".join(answers))


if __name__ == "__main__":
    main()