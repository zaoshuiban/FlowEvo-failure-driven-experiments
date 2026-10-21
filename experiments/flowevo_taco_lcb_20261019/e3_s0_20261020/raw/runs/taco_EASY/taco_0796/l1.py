def even_magic(n):
    total = n * n + 1
    square = []

    for i in range(n):
        row = []
        for j in range(n):
            value = i * n + j + 1
            if i % 4 == j % 4 or (i % 4) + (j % 4) == 3:
                value = total - value
            row.append(value)
        square.append(row)

    return square