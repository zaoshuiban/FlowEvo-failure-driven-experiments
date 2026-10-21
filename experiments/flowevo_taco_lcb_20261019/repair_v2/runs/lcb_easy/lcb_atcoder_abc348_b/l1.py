import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    points = []
    idx = 1

    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        idx += 2
        points.append((x, y))

    answers = []

    for i in range(n):
        xi, yi = points[i]
        best_dist = -1
        best_id = -1

        for j in range(n):
            if i == j:
                continue

            xj, yj = points[j]
            dx = xi - xj
            dy = yi - yj
            dist = dx * dx + dy * dy
            point_id = j + 1

            if dist > best_dist or (dist == best_dist and point_id < best_id):
                best_dist = dist
                best_id = point_id

        answers.append(str(best_id))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()