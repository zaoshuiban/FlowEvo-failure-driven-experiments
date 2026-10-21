import math

def vector_length(vector):
    try:
        (x1, y1), (x2, y2) = vector
    except (TypeError, ValueError):
        x1, y1, x2, y2 = vector

    try:
        dx = x2 - x1
        dy = y2 - y1
    except TypeError:
        x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
        dx = x2 - x1
        dy = y2 - y1

    return math.hypot(dx, dy)