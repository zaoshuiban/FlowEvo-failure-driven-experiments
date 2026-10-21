import math

def vector_length(vector):
    (x1, y1), (x2, y2) = vector
    return math.hypot(x2 - x1, y2 - y1)